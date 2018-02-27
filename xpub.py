#!/usr/bin/env python3

import sys
import os
import re
import datetime
import qrcode
import io
import random
import base64
import json
import time

#dataset
import dataset
from stuf import stuf

# Bottle
from bottle import Bottle, route, request, response, get, abort, debug, template, static_file, redirect

# MTServer - Multi Threaded wsgi server
from mtbottle import MTServer

# Paste - Multi Threaded wsgi server
from paste import httpserver


#bitcoin stuff
import pycoin.key
os.environ["PYCOIN_NATIVE"]="openssl"
from cashaddress import convert

import verify_tx
import exchangerate

debug(True)

db_name = 'sqlite:///pyxpub.db?check_same_thread=False'


# Look for the directory containing the configuration files
def find_data_dir():
  lib_dir = os.path.dirname(os.path.abspath(__file__))
  data_dir_locations = [
    os.path.join(os.path.expanduser('~'), '.xpub'),
    os.path.join(os.path.expanduser('~'), '.config', 'xpub'),
    lib_dir,
    os.getcwd()
  ]
  if len(sys.argv) > 1:
    if sys.argv[1] == '-h' or sys.argv[1] == '--help':
      print(usage)
      sys.exit(0)
    else:
      data_dir_locations.insert(0, os.path.abspath(sys.argv[1]))
      if not os.path.isdir(data_dir_locations[0]):
        print('No such directory: ' + data_dir_locations[0])
  for data_dir in data_dir_locations:
    try:
      os.chdir(data_dir)
    except (OSError, NotADirectoryError):
      continue
    if os.path.isfile('key.list'):
      print('Using {dir} as data directory'.format(dir=data_dir))
      break
    
def init_db():
  db = dataset.connect(db_name, row_type=stuf)
    
  return db

def get_wallet_index():
  _db = init_db()
  _id = 0
  results = _db.query('SELECT MAX(id) as id FROM payment_requests')
  for result in results:
    #print(result.id)
    _id = result.id
  
  return _id

# Read the xpub key from  key.list file
def get_xpub():
  _xpub = 0
  try:
    f = open('key.list', 'r')
    for line in f.readlines():
      _key = line.strip()
      pattern = re.compile("xpub")
      if pattern.match(_key, 0):
        _xpub = pycoin.key.Key.from_text(_key)
        f.close()
        return _xpub
    f.close()
    if _xpub == 0:
      print('ERROR: No xpub in key.list')
      sys.exit(2)
  except (IOError, OSError, FileNotFoundError, PermissionError):
    print('ERROR: Could not open key.list')
    sys.exit(2)

# Derive address from xpub key and increment address index
def get_xpub_address(xpub, index):
  # 0 => public addresses
  # 1 => change addresses, only for internal use
  account_type = 0
  xpub_subkey = xpub.subkey(account_type)
  addr = xpub_subkey.subkey(index).bitcoin_address()
  caddr = convert.to_cash_address(addr)
  #print(caddr)
  
  #return caddr.upper()
  return caddr

def get_payment_by_ip(ip):
  _db = init_db()
  _table = _db['payment_requests']
  _payment = _table.find_one(ip=ip)
  if _payment:
    return _payment
  else:
    return False
  
def get_payment_by_label(label):
  _db = init_db()
  _table = _db['payment_requests']
  _payment = _table.find_one(label=label)
  if _payment:
    return _payment
  else:
    return False
  
def get_payment_by_addr(addr):
  _db = init_db()
  _table = _db['payment_requests']
  _payment = _table.find_one(addr=addr)
  if _payment:
    return _payment
  else:
    return False

def update_payment_received(payment_id, received, txid):
  _db = init_db()
  _table = _db['payment_requests']

  _table.update(dict(id=payment_id, received=received, txid=txid), ['id'])
  
def get_address(ip_addr, amount="", label=""):
  _payment = False
  #if ratelimit_ip:
    #_payment = get_payment_by_ip(ip_addr)
  #if ratelimit_label and label:
    #_payment = get_payment_by_label(label)
  
  if _payment:
    _addr =  _payment.addr
    return _addr
  else:
    _xpub = get_xpub()
    _index = get_wallet_index()
    _addr = get_xpub_address(_xpub, _index)
    with dataset.connect(db_name, row_type=stuf) as tx:
      tx['payment_requests'].insert(dict(timestamp=time.time(), ip=ip_addr, addr=_addr, amount=amount, label=label, received=0, confirmations=0, txid="NoTX"))
    return _addr
  
def generate_payment(parameters, ip_addr):
  _amount = False
  _label = False
  _payment = False
  _uri = ""
  _uri_params = ""
  _qr = "/qr?addr="
  _qr_params = ""
  
  if 'amount' in parameters:
    _amount = parameters.amount
    _qr_params += "&amount=" + _amount
    _uri_params += "?amount=" + _amount
  else:
    abort(400, "Specify an amount!")
  if 'label' in parameters:
    _label = parameters.label
    _qr_params +=  "&label=" + _label
    if _amount:
      _uri_params += "&message=" + _label
    else:
      _uri_params += "?message=" + _label
  
  _addr = get_address(ip_addr, _amount, _label)
  _legacy = convert.to_legacy_address(_addr)
  _qr += _addr + _qr_params
  _uri = _addr + _uri_params

  _payreq = {
    "payment": {
      "amount": _amount,
      #"addr": _addr.lstrip('BITCOINCASH:'),
      "addr": _addr,
      "legacy_addr": _legacy,
      "label": _label,
      "qr_img": _qr,
      "payment_uri": _uri,
    }
  }
  
  _json = json.dumps(_payreq)
  return _json

# Generate QR code and return the image
def get_qr(parameters):
  _addr = False
  _amount = False
  _label = False
  _data = ""
  
  if 'addr' in parameters:
     _addr = parameters.addr.upper()
     #_addr = parameters['addr'][0].rstrip('/')
     _data = _addr
  else:
    abort(401, "Specify address")
     
  if 'amount' in parameters and 'label' in parameters:
    _amount = parameters.amount
    _label = parameters.label
    _data += "?amount=" + _amount
    _data += "&message=" + _label
  elif 'amount' in parameters:
     _amount = parameters.amount
     _data += "?amount=" + _amount
  elif 'label' in parameters:
     _label = parameters.label
     _data += "?message=" + _label
     
  #print(_data)
     
  qr = qrcode.QRCode(
    error_correction=qrcode.constants.ERROR_CORRECT_L,
    border=2,
  )
  qr.add_data(_data)
#  qr.add_data(parameters['addr'][0].rstrip('/'))
  qr.make(fit=True)
  img = qr.make_image()
  
  return img

def generate_embed(addr, parameters):
  _amount = False
  _label = False
  _qruri = "/qr?addr=" + addr
  _copy = addr
  _amount_label = ""
  
  if 'amount' in parameters:
    _amount = parameters.amount
    _qruri += "&amount=" + _amount
    _amount_label += "AMOUNT: " + _amount + " BCH "
    _copy += "?amount=" + _amount
  if 'label' in parameters:
    _label = parameters.label
    _qruri += "&label=" + _label
    _amount_label += "LABEL: " + _label + " "
    if _amount:
      _copy += "&message=" + _label
    else:
      _copy += "?message=" + _label

  filler = {
    'addr': addr,
    'qruri' : _qruri,
    'label' : _amount_label,
    'copy' : _copy,
  }
  html = template('views/qr.html').format(**filler)

  return html

def generate_ledger(parameters, ip_addr):
  _db = init_db()
  _ledger = {}
  
  for _payment in _db['payment_requests']:
    _data = {
              'id': _payment.id,
              'timestamp': _payment.timestamp,
              'addr': _payment.addr,
              'amount': _payment.amount,
              'label': _payment.label,
              'received': _payment.received,
              'confirmations': _payment.confirmations,
              'txid': _payment.txid,
            }
    _ledger[str(_payment.id)] = _data
    
  _json = json.dumps(_ledger)
  return _json

def generate_verify(parameters, ip_addr):
  _addr = False
  _amount = False
  _label = False
  _received = False
  _payment = False
  
  # Find payment by label, if not verified, set parameters
  if 'label' in parameters:
    _payment = get_payment_by_label(parameters.label)
    if not _payment:
      abort(400, "ERROR: Unknown Label! - " + parameters.label)
  # Find payment by addr, if not verified, set parameters
  elif 'addr' in parameters and 'amount' in parameters:
    _amount = parameters.amount
    if convert.is_valid(parameters.addr):
      _addr = parameters.addr
      _payment = get_payment_by_addr(_addr)
      if not _payment:
        abort(400, "ERROR: Unknown Payment Address! - " + _addr)
    else:
      abort(400, "Invalid address!")
  else:
    abort(400, "Incorrect use of API, RTFM!")
    
  # TODO: return more payment details. see verify_tx.verify()
  if _payment.received == 1:
    return json.dumps({"received": 1})
  else:
    _addr = _payment.addr
    _amount = _payment.amount
    _label = _payment.label
  
  # If payment not received yet, rescan
  _received = verify_tx.verify(_addr, _amount)
  
  # If rescan has positive result, update payment record in database
  if _received['received'] == 1 and _payment.received == 0:
    update_payment_received(_payment.id, 1, _received['txid'])

  # Return verification result
  if _received:
    return json.dumps(_received)
  else:
    return json.dumps({"received": 0})
  
def generate_rate(parameters, ip_addr):
  _currency = ""
  _source = ""
  if 'currency' in parameters and 'source' in parameters:
    if not exchangerate.is_supported(parameters.currency, parameters.source):
      abort(400, "ERROR: Unsupported Currency! => " + parameters.currency)
    else:
      _r = exchangerate.get_rate(parameters.currency, parameters.source)
      _price = {
          'currency': _r.currency,
          'price'   : _r.rate,
        }
      return _price
  # TODO: Error handling is_supported()
  elif 'source' in parameters:
    _r = exchangerate.get_currencies(parameters.source)
    return _r
  else:
    _r = exchangerate.get_sources()
    return _r

  

def set_headers(environ):
  if  'HTTP_ORIGIN' in environ:
    origin = environ['HTTP_ORIGIN']
    response.set_header("Access-Control-Allow-Origin", str(origin))
    response.set_header("Access-Control-Allow-Credentials", "true")
  #response.set_header("Access-Control-Allow-Origin", "*")
  #response.set_header("Access-Control-Allow-Credentials", "true")

# Init bottle framework
app = application = Bottle()

@app.route('/')
@app.route('/react')
def root():
  redirect("/react/")

@app.route('/embed')
def embed():
  set_headers(request.environ)
  response.content_type = 'text/html; charset=utf-8' 
  
  _ip = request.environ.get('REMOTE_ADDR')
  _parameters = request.query
  
  _addr = get_address(_ip)
  _html = generate_embed(_addr, _parameters)
  
  return _html

@app.route('/qr')
def qr():
  set_headers(request.environ)
  response.content_type = 'image/png'
  
  _ip = request.environ.get('REMOTE_ADDR')
  _parameters = request.query
  _qr = get_qr(_parameters)
  _output = io.BytesIO()
  _qr.save(_output, format='PNG')
  
  return _output.getvalue()
  
@app.route('/api/payment')
def payment():
  set_headers(request.environ)
  response.content_type = 'application/json'
  
  _ip = request.environ.get('REMOTE_ADDR')
  _parameters = request.query
  _payment = generate_payment(_parameters, _ip)
  
  return _payment
  
@app.route('/api/verify')
def verify():
  set_headers(request.environ)
  response.content_type = 'application/json'
  
  _ip = request.environ.get('REMOTE_ADDR')
  _parameters = request.query
  _verify = generate_verify(_parameters, _ip)
  
  return _verify
  
@app.route('/api/ledger')
def ledger():
  set_headers(request.environ)
  response.content_type = 'application/json'
  
  _ip = request.environ.get('REMOTE_ADDR')
  _parameters = request.query
  _ledger = generate_ledger(_parameters, _ip)
  
  return _ledger

@app.route('/api/rate')
def rate():
  set_headers(request.environ)
  response.content_type = 'application/json'
  
  _ip = request.environ.get('REMOTE_ADDR')
  _parameters = request.query
  _rate = generate_rate(_parameters, _ip)
  
  return _rate

# Serve static files
@app.route('/static/<filename:path>')
def send_static(filename):
  set_headers(request.environ)
  return static_file(filename, root="static/")

@app.route('/react/', strict_slashes=False)
@app.route('/react/<filename:path>')
def react(filename='index.html'):
  set_headers(request.environ)
  return static_file(filename, root="react/")


def main():
  # init
  find_data_dir()
  index = get_wallet_index()
  xpub = get_xpub()
  print('Wallet using xpub key: ' + xpub.as_text()[:20] + '...' + xpub.as_text()[-8:])
  print('Starting wallet at index: ' + str(index))
  
  # MTServer wsgi server
  app.run(server=MTServer, host='0.0.0.0', port=8080, thread_count=3)
  
  # Paste wsgi server
  #httpserver.serve(app, host='0.0.0.0', port=8080)
  
  #start_server()
  

if __name__ == "__main__":
  main()

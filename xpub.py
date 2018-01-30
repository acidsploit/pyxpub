#!/usr/bin/env python3

import sys
import os
import requests
import re

from wsgiref.simple_server import make_server
import urllib.parse
import datetime
import qrcode
import io
import random
import base64

import pycoin.key
os.environ["PYCOIN_NATIVE"]="openssl"
from cashaddress import convert

usage = '''Usage: xpub [DATA_DIRECTORY]
See the README file for more information.'''
 
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

# Read index file or create one if it does not exist
def get_index():
  try:
    f = open('index', 'r')
    for line in f.readlines():
      _ix = line.strip()
      pattern = re.compile("(\d+)")
      if pattern.match(_ix):
        index = int(_ix)
        f.close()
        return index
    f.close()
  except (IOError, OSError, FileNotFoundError, PermissionError):
    if FileNotFoundError:
      index = 0
      print('Could not find index file. Creating a new one. Assuming index = ' + str(index))
      f = open('index', 'w+')
      f.write(str(index))
      f.close()
      return index
    else:
      print('Could not open index file. Check permissions.')
      sys.exit(2)

# Read the xpub key from  key.list file
def get_xpub():
  xpub = 0
  try:
    f = open('key.list', 'r')
    for line in f.readlines():
      _key = line.strip()
      pattern = re.compile("xpub")
      if pattern.match(_key, 0):
        xpub = pycoin.key.Key.from_text(_key)
        f.close()
        return xpub
    f.close()
    if xpub == 0:
      print('No xpub in key.list')
      sys.exit(2)
  except (IOError, OSError, FileNotFoundError, PermissionError):
    print('Could not open key.list')
    sys.exit(2)

# Derive address from xpub key and increment address index
def get_xpub_address(xpub, index):
  # 0 => public addresses
  # 1 => change addresses, only for internal use
  account_type = 0
  xpub_subkey = xpub.subkey(account_type)
  addr = xpub_subkey.subkey(index).bitcoin_address()
  caddr = convert.to_cash_address(addr)
  
  # increment index
  f = open('index', 'w+')
  index += 1
  f.write(str(index))
  f.close()
  
  return(caddr)

# Generate QR code and return the image
def get_qr(parameters):
  qr = qrcode.QRCode(
    error_correction=qrcode.constants.ERROR_CORRECT_L,
    border=2,
  )
  qr.add_data(parameters['addr'][0].upper().rstrip('/'))
#  qr.add_data(parameters['addr'][0].rstrip('/'))
  qr.make(fit=True)
  img = qr.make_image()
  
  return img

# Check if requesting ip already generated a qr code, re-use previously generated address.
# This is done to prevent snooping and page reloads to waste addresses.
# You can setup a cron job to delete ip.list to wipe ip history at desired interval.
def check_ip(ip):
  try:
    f = open('ip.list', 'r')
    for line in f.readlines():
      _pair = line.split('/')
      if _pair[0] == ip:
        f.close()
        # return bitcoin address linked to ip
        return _pair[1].strip('\n')
    f.close()
    return False
  except (FileNotFoundError):
    print("File ip.list not found! Creating new one.")
    f = open('ip.list', 'w+')
    f.close()
    return False

# Utility wrapper function
def load_file(filename):
  try:
    src = open(filename, 'r')
  except (IOError, OSError, FileNotFoundError, PermissionError):
    src = open(os.path.join(lib_dir, filename), 'r')
  data = src.read()
  src.close()
  return data
  
def generate_qr_html(addr):
  filler = {
    'addr': addr,
  }
  html = load_file('assets/qr.html').format(**filler)

  return html

def webapp(environ, start_response):
  if 'HTTP_X_REAL_IP' in environ:
    environ['REMOTE_ADDR'] = environ['HTTP_X_REAL_IP']
  ip_addr = environ['REMOTE_ADDR']
  
  request = environ['PATH_INFO'].lstrip('/').split('/')[-1]
  parameters = urllib.parse.parse_qs(environ['QUERY_STRING'])
  
  if request == 'qr':
    if convert.is_valid(parameters['addr'][0].rstrip('/')):
      status = '200 OK'
      headers = [('Content-type', 'image/png')]
      start_response(status, headers)
      
      img = get_qr(parameters)
      output = io.BytesIO()
      img.save(output, format='PNG')
      page = output.getvalue()
    else :
      status = '200 OK'
      headers = [('Content-type', 'text/html')]
      start_response(status, headers)
      message = "Invalid Address!"
      page = message.encode('utf-8')
  elif request.endswith('.js'):
    status = '200 OK'
    headers = [('Content-type', 'text/javascript')]
    start_response(status, headers)
    
    req = load_file(os.path.join('assets', request))
    page = req.encode('utf-8')
  elif request.endswith('.css'):
    status = '200 OK'
    headers = [('Content-type', 'text/css')]
    start_response(status, headers)
    
    #req = load_file(os.path.join('assets', request))
    req = ''
    page = req.encode('utf-8')
  else:
    status = '200 OK' # HTTP Status
    headers = [('Content-type', 'text/html; charset=utf-8')]  # HTTP Headers
    start_response(status, headers)
    
    addr = check_ip(ip_addr)
    if addr:
      print("REUSE - " + ip_addr + " - " + addr)
      html = generate_qr_html(addr)
      page = html.encode('utf-8')
    else:
      index = get_index()
      xpub = get_xpub()
      addr = get_xpub_address(xpub, index)
    
      f = open('ip.list', 'a')
      f.write(ip_addr + '/' + addr + '\n')
      f.close()
      
      print("NEW - " + ip_addr + " - " + addr)
      html = generate_qr_html(addr)
      page = html.encode('utf-8')
  
  return [page]

def start_server():
  with make_server('', 8080, webapp) as httpd:
    print("Serving on port 8080...")
    # Serve until process is killed
    httpd.serve_forever()

def main():
  find_data_dir()
  index = get_index()
  #xpub = get_xpub()
  #addr = get_xpub_address(xpub, index)
  #print(addr)
  start_server()
  

if __name__ == "__main__":
  main()

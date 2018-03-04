#!/usr/bin/env python3

#import urllib.request
import requests
import json
import random
import sys
import os

#bitcoin stuff
import pycoin.key
os.environ["PYCOIN_NATIVE"]="openssl"
from cashaddress import convert

#dataset
import dataset
from stuf import stuf

explorers = [
  {
    'api_addr': 'https://blockdozer.com/insight-api/addr/{caddr}',
    'api_tx': 'https://blockdozer.com/insight-api/tx/',
  },
  {
    'api_addr': 'https://bch-insight.bitpay.com/api/addr/{caddr}',
    'api_tx': 'https://bch-insight.bitpay.com/api/tx/',
  },
  # Needs legacy address
  #{
    #'api_addr': 'https://cashexplorer.bitcoin.com/api/addr/{legacy}',
    #'api_tx': 'https://cashexplorer.bitcoin.com/api/tx/',
  #},
  {
    'api_addr': 'https://bccblock.info/api/addr/{legacy}',
    'api_tx': 'https://bccblock.info/api/tx/',
  },
  {
    'api_addr': 'https://bitcoincash.blockexplorer.com/api/addr/{legacy}',
    'api_tx': 'https://bitcoincash.blockexplorer.com/api/tx/',
  },
  
  
]

def randomize():
  rand = random.randint(0, len(explorers)-1)
  api = explorers[rand]
  
  return api

def get_api_addr(addr):
  _legacy = convert.to_legacy_address(addr)
  _addr = {
    'caddr': addr,
    'legacy': _legacy,
  }
  
  _api = randomize()
  
  _request = _api['api_addr'].format(**_addr)
  print(_request)
  _r = requests.get(_request)
  _json_addr = _r.json()
  
  return _json_addr
  
def get_api_tx(tx):
  _api = randomize()
  _request = _api['api_tx'] + tx
  print(_request)
  _r = requests.get(_request)
  _json_tx = _r.json()
  
  return _json_tx

def verify_tx(addr):
  _legacy = convert.to_legacy_address(addr)
  _addr = {
    'caddr': addr,
    'legacy': _legacy,
  }
  _json_addr = get_api_addr(addr)
  _amount = _json_addr['unconfirmedBalance'] if _json_addr['unconfirmedBalance'] != 0 else _json_addr['totalReceived']
  
  #print(json.dumps(_json_addr, indent=4))
  
  if len(_json_addr['transactions']) == 1:
    print('tx: ' + _json_addr['transactions'][0])
    _txid = _json_addr['transactions'][0]
    _request = api_tx + _txid
    _r = requests.get(_request)
    _json_tx = _r.json()
    #print(json.dumps(_json_tx, indent=4))
    for _out in _json_tx['vout']:
      if float(_out['value']) == _amount:
        if _legacy == _out['scriptPubKey']['addresses'][0] or addr.lstrip('bitcoincash:') == _out['scriptPubKey']['addresses'][0]:
          print('FOUND!')
          print(_out['value'])
          _tx = {
            "value": _amount,
            "input_address": addr,
            "confirmations": _json_tx['confirmations'],
            "transaction_hash": _txid,
            "input_transaction_hash": _txid,
            "destination_address": addr,
            }
          return _tx

  return False

def verify_tx_with_amount(addr, amount):
  _legacy = convert.to_legacy_address(addr)

  _json_addr = get_api_addr(addr)
  
  #print(json.dumps(_json_addr, indent=4))
  
  if len(_json_addr['transactions']) > 0:
    for _txid in _json_addr['transactions']:
      print('txid: ' + _txid)
      _json_tx = get_api_tx(_txid)
      #print(json.dumps(_json_tx, indent=4))
      for _out in _json_tx['vout']:
        if float(_out['value']) == float(amount):
          if _legacy == _out['scriptPubKey']['addresses'][0] or addr.lstrip('bitcoincash:') == _out['scriptPubKey']['addresses'][0]:
            print('FOUND!')
            print(_out['value'])
            _tx = {
              "value": amount,
              "input_address": addr,
              "confirmations": _json_tx['confirmations'],
              "transaction_hash": _txid,
              "input_transaction_hash": _txid,
              "destination_address": addr,
              }
            return _tx

  return False

def verify(addr, amount):
  _legacy = convert.to_legacy_address(addr)
  _json_addr = get_api_addr(addr)
  
  if _json_addr['unconfirmedBalance'] == float(amount) or _json_addr['balance'] == float(amount):
    for _txid in _json_addr['transactions']:
      print('txid: ' + _txid)
      _json_tx = get_api_tx(_txid)
      for _out in _json_tx['vout']:
        if float(_out['value']) == float(amount):
          if _legacy == _out['scriptPubKey']['addresses'][0] or addr.lstrip('bitcoincash:') == _out['scriptPubKey']['addresses'][0]:
            print('FOUND!')
            print(_out['value'])
            _tx = {
              "received": 1,
              "receive_address": addr,
              "amount": amount,
              "confirmations": _json_tx['confirmations'],
              "txid": _txid,
              }
            return _tx
  
  return {"received": 0}


def callback(addr, callbackurl, amount=False):
  _tx = False
  _callback = callbackurl
  if addr and amount:
    _tx = verify_tx_with_amount(addr, amount)
  else:
    _tx = verify_tx(addr)
    
  if _tx:
    _callback += '&value=' + _tx['value'] 
    _callback += '&input_address=' + _tx['input_address']
    _callback += '&confirmations' + _tx['confirmations']
    _callback += '&transaction_hash' + _tx['transaction_hash']
    _callback += '&input_transaction_hash' + _tx['input_transaction_hash']
    _callback += '&destination_address' + _tx['destination_address']
    
    _r = requests.get(_callback)
    return True
  else:
    return False


def main():
  _addr = ""
  _amount = False
  _callback = False
  _tx = False
  
  try:
    _addr = sys.argv[1]
  except:
    print('No address to check!')
    sys.exit(2)
    
  try:
    _amount = sys.argv[2]
  except:
    _amount = False
    
  try:
    _callback = sys.argv[3]
  except:
    _callback = False
    
  #print('addr: ' + _addr)
  #print('amnt: ' + str(_amount))
  
  if _amount:
    _tx = verify_tx_with_amount(_addr, _amount)
    print(_tx)
  else:
    _tx = verify_tx(_addr)
    
  #if _tx and _callback:
    #callback(_addr, _callback, )

if __name__ == '__main__':
  main()

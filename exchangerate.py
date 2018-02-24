#!/usr/bin/env python3

#import urllib.request
import requests
import json
import random
import sys
import os
import time

#bitcoin stuff
#import pycoin.key
#os.environ["PYCOIN_NATIVE"]="openssl"
#from cashaddress import convert

#dataset
import dataset
from stuf import stuf

db_name = 'sqlite:///pyxpub.db?check_same_thread=False'

CRYPTOCOMPARE = ["EUR", "USD", "GBP", "AUD", "BRL", "CAD", "CHF", "CLP", "CNY", "CZK", "DKK", "HKD", "HUF", "IDR", "ILS", "INR", "JPY", "KRW", "MXN", "MYR", "NOK", "NZD", "PHP", "PKR", "PLN", "RUB", "SEK", "SGD", "THB", "TRY", "TWD", "ZAR"]

COINBASE = ["EUR", "USD"]

KRAKEN = ["EUR", "USD"]


def is_supported(currency, source):
  _db = dataset.connect(db_name, row_type=stuf)
  _table = _db[source]
  _record = _table.find_one(currency=currency)   
   
  if _record:
    return True
  else:
    return False  
  
def get_currencies(source):
  if source == "cryptocompare":
    return {'currencies': CRYPTOCOMPARE}
  elif source == "coinbase":
    return {'currencies': COINBASE}
  elif source == "kraken":
    return {'currencies': KRAKEN}

def update_cryptocompare():
  _db = dataset.connect(db_name, row_type=stuf)
  _table = _db['cryptocompare']
  
  _api = "https://min-api.cryptocompare.com/data/price?fsym=BCH&tsyms={currencies}"
  _string = ','.join(map(str, CRYPTOCOMPARE))
  _currencies = {'currencies': _string}
  _query = _api.format(**_currencies)
  
  print("PYXPUB - FETCH: " + _query)
  _response = requests.get(_query)
  _json = _response.json()
  
  for key in _json:
    _record = _table.find_one(currency=key)
    if not _record:
      print('INSERT: ' + key)
      with dataset.connect(db_name, row_type=stuf) as tx:
        tx['cryptocompare'].insert(dict(currency=key, rate=_json[key], timestamp=time.time()))
    else:
      _table.update(dict(currency=key, rate=_json[key], timestamp=time.time()), ['currency'])
      #print('UPDATE: ' + key)
      
def update_coinbase():
  _db = dataset.connect(db_name, row_type=stuf)
  _table = _db['coinbase']
  
  _api = "https://min-api.cryptocompare.com/data/price?fsym=BCH&tsyms={currencies}&e=Coinbase"
  _string = ','.join(map(str, COINBASE))
  _currencies = {'currencies': _string}
  _query = _api.format(**_currencies)
  
  print("PYXPUB - FETCH: " + _query)
  _response = requests.get(_query)
  _json = _response.json()
  
  for key in _json:
    _record = _table.find_one(currency=key)
    if not _record:
      print('INSERT: ' + key)
      with dataset.connect(db_name, row_type=stuf) as tx:
        tx['coinbase'].insert(dict(currency=key, rate=_json[key], timestamp=time.time()))
    else:
      _table.update(dict(currency=key, rate=_json[key], timestamp=time.time()), ['currency'])
      #print('UPDATE: ' + key)
      
def update_kraken():
  _db = dataset.connect(db_name, row_type=stuf)
  _table = _db['kraken']
  
  _api = "https://min-api.cryptocompare.com/data/price?fsym=BCH&tsyms={currencies}&e=Kraken"
  _string = ','.join(map(str, KRAKEN))
  _currencies = {'currencies': _string}
  _query = _api.format(**_currencies)
  
  print("PYXPUB - FETCH: " + _query)
  _response = requests.get(_query)
  _json = _response.json()
  
  for key in _json:
    _record = _table.find_one(currency=key)
    if not _record:
      print('INSERT: ' + key)
      with dataset.connect(db_name, row_type=stuf) as tx:
        tx['kraken'].insert(dict(currency=key, rate=_json[key], timestamp=time.time()))
    else:
      _table.update(dict(currency=key, rate=_json[key], timestamp=time.time()), ['currency'])
      #print('UPDATE: ' + key)
  

def get_rate(currency, source):
  _db = dataset.connect(db_name, row_type=stuf)
  _table = _db[source]
  _record = _table.find_one(currency=currency)
  _now = time.time()
  
  if source == "cryptocompare":
    if not _record:
      print("PYXPUB - TABLE: {} ENTRY: {} NOT FOUND - UPDATING".format(source, currency))
      update_cryptocompare()
      _record = _table.find_one(currency=currency)
    else:
      if ((_now - _record.timestamp) > 30):
        print("PYXPUB - TABLE {} OUTDATED - UPDATING".format(source))
        update_cryptocompare()
        _record = _table.find_one(currency=currency)
      else:
        _record = _table.find_one(currency=currency)
  
  elif source == "coinbase":
    if not _record:
      print("PYXPUB - TABLE: {} ENTRY: {} NOT FOUND - UPDATING".format(source, currency))
      update_coinbase()
      _record = _table.find_one(currency=currency)
    else:
      if ((_now - _record.timestamp) > 30):
        print("PYXPUB - TABLE {} OUTDATED - UPDATING".format(source))
        update_coinbase()
        _record = _table.find_one(currency=currency)
      else:
        _record = _table.find_one(currency=currency)
        
  elif source == "kraken":
    if not _record:
      print("PYXPUB - TABLE: {} ENTRY: {} NOT FOUND - UPDATING".format(source, currency))
      update_kraken()
      _record = _table.find_one(currency=currency)
    else:
      if ((_now - _record.timestamp) > 30):
        print("PYXPUB - TABLE {} OUTDATED - UPDATING".format(source))
        update_kraken()
        _record = _table.find_one(currency=currency)
      else:
        _record = _table.find_one(currency=currency)
      
  return _record



def main():
  _curr = "USD"
  
  try:
    _curr = sys.argv[1]
  except:
    print('No currency specified. Using: ' + _curr)
    
  _ticker = get_live_ticker(_curr)

  print("{:.2f}".format(float(_ticker['price_' + _curr.lower()])))
  
  update_cryptocompare()
  
  #for f in fiat:
    #_ticker = get_live_ticker(f)
    #print("%3s: %.2f" % (f, float(_ticker[0]['price_' + f.lower()])))

if __name__ == '__main__':
  main()

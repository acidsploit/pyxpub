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

SOURCES = {
  'cryptocompare': ["EUR", "USD", "GBP", "AUD", "BRL", "CAD", "CHF", "CLP", "CNY", 
                    "CZK", "DKK", "HKD", "HUF", "IDR", "ILS", "INR", "JPY", "KRW", 
                    "MXN", "MYR", "NOK", "NZD", "PHP", "PKR", "PLN", "RUB", "SEK", 
                    "SGD", "THB", "TRY", "TWD", "ZAR"],
  'coinmarketcap': ["EUR", "USD", "GBP", "AUD", "BRL", "CAD", "CHF", "CLP", "CNY", 
                    "CZK", "DKK", "HKD", "HUF", "IDR", "ILS", "INR", "JPY", "KRW", 
                    "MXN", "MYR", "NOK", "NZD", "PHP", "PKR", "PLN", "RUB", "SEK", 
                    "SGD", "THB", "TRY", "TWD", "ZAR"],
  'kraken':        ["EUR", "USD"],
  'coinbase':      ["EUR", "USD"],
  'bitstamp':      ["EUR", "USD"],
  'coinfloor':     ["GBP"],
  'bitbay':        ["EUR", "USD", "PLN"],
  'bitflip':       ["RUB", "USD", "UAH"],
  }


def is_supported(currency, source):
  if source in SOURCES:
    if currency in SOURCES[source]:
      return True

  return False

  
def get_currencies(source):
  if source in SOURCES:
    return {'currencies': SOURCES[source]}
  
def get_sources():
  _keys = []
  for key in SOURCES:
    _keys.append(key)
    
  return {'sources': _keys}

def update_coinmarketcap(currency):
  _db = dataset.connect(db_name, row_type=stuf)
  _table = _db['coinmarketcap']
  
  _api = "https://api.coinmarketcap.com/v1/ticker/bitcoin-cash/?convert={}"
  _query = _api.format(currency)
  
  print("PYXPUB - FETCH: " + _query)
  _response = requests.get(_query)
  _json = _response.json()
  
  _price = _json[0]['price_' + currency.lower()]
  
  _record = _table.find_one(currency=currency)
  if not _record:
    print('PYXPUB - INSERT: ' + currency)
    with dataset.connect(db_name, row_type=stuf) as tx:
      tx['coinmarketcap'].insert(dict(currency=currency, rate=_price, timestamp=time.time()))
  else:
    _table.update(dict(currency=currency, rate=_price, timestamp=time.time()), ['currency'])
    print('PYXPUB - UPDATE: ' + currency)
    
  
def update_db(source, currency):
  _db = dataset.connect(db_name, row_type=stuf)
  _table = _db[source]
  
  if source == 'coinmarketcap':
    update_coinmarketcap(currency)
    return 0
  
  if source == 'cryptocompare':
    _api = "https://min-api.cryptocompare.com/data/price?fsym=BCH&tsyms={currencies}"
  else:
    _api = "https://min-api.cryptocompare.com/data/price?fsym=BCH&tsyms={currencies}&e={source}"
  
  _string = ','.join(map(str, SOURCES[source]))
  _filler = {'currencies': _string,
             'source': source
            }
  _query = _api.format(**_filler)
  
  print("PYXPUB - FETCH: " + _query)
  _response = requests.get(_query)
  _json = _response.json()
  
  for key in _json:
    _record = _table.find_one(currency=key)
    if not _record:
      print('PYXPUB - INSERT: ' + key)
      with dataset.connect(db_name, row_type=stuf) as tx:
        tx[source].insert(dict(currency=key, rate=_json[key], timestamp=time.time()))
    else:
      _table.update(dict(currency=key, rate=_json[key], timestamp=time.time()), ['currency'])
      #print('UPDATE: ' + key)

def get_rate(currency, source):
  _db = dataset.connect(db_name, row_type=stuf)
  _table = _db[source]
  _record = _table.find_one(currency=currency)
  _now = time.time()
  
  if source in SOURCES:
    if not _record:
      print("PYXPUB - TABLE: {} ENTRY: {} NOT FOUND - UPDATING".format(source, currency))
      update_db(source, currency)
      _record = _table.find_one(currency=currency)
    else:
      if ((_now - _record.timestamp) > 30):
        print("PYXPUB - TABLE {} OUTDATED - UPDATING".format(source))
        update_db(source, currency)
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

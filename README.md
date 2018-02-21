# pyxpub - Private Payment Gateway
 
Pyxpub is a simple webapp that generates unique payment requests for Bitcoin Cash. It exposes the needed features of a receive-only wallet through a JSON API to enable quick development of Point-of-Sale systems. This without the developer having to worry about the sensitive bits. Pyxpub makes it easy to follow Bitcoin best practices and future-proofs your application in order to scale towards future needs.

Pyxpub also includes a Point-of-Sale app by default. Check out the demo at https://pos.devzero.be

## Introduction
As per Bitcoin best practices it is preferred to use a new receiving address for each payment. This for security and privacy implications for both you and your customers or donators. Also, we do not want any private keys on the server generating the receiving address, nor would we want them on any PoS system. This can easily be achieved by using an hd-wallet as described in [BIP32](https://github.com/bitcoin/bips/blob/master/bip-0032.mediawiki). This is the default wallet type when you create a new wallet with [Electron Cash](https://electroncash.org/).

### pyxpub
Pyxpub exposes the needed features of that wallet through an easy to use JSON API, this to enable quick Point-of-Sale developement, without having to worry about the sensitive bits. Pyxpub handles the generation of new unique addresses for payment requests and keeps track of those, monitor payments requests for incoming transactions, and keeps a sales ledger. All you need to do is call the right api endpoints to get it all in your app.

All generated Bitcoin Cash addresses are derived from a pre-defined (Electron Cash) xpub key. Address re-use is prevented by keeping track of used addresses.

### xpub (Electron Cash)
First, when you create a new wallet with Electron Cash, it is very important to propperly backup and safely store your mnemonic seed. This Electron wallet is your full (send & receive) wallet, make sure it is password protected and also stored safely. You will use it later to retrieve payments. The webapp will use the xpub key to generate receive only addresses on the server, corresponding to the addresses from your Electron wallet. This way we don't need private keys on the server. You can find your wallet's master public key or xpub key through the 'Wallet -> Information' menu.

## Installation (built in server)
__clone repo__

    git clone https://github.com/acidsploit/pyxpub.git pyxpub

__setup environment__

    cd pyxpub/
    bash setup.sh

__set xpub key__

Copy your xpub key from an Electron Cash wallet and paste it in the key.list file.

    echo 'xpub...' > key.list

__run__

    cd pyxpub/
    bash pyxpub.sh

__access locally__

Browse to http://localhost:8080;

## Installation (uWSGI + NGINX)
__install nginx, uwsgi and uwsgi python plugin__

Follow your distributions directions to install these packages.

__insall pyxpub in appropriate location__

    cd /srv/http/
    git clone https://github.com/acidsploit/pyxpub.git pyxpub
    
    cd pyxpub/
    bash setup.sh
    echo 'xpub...' > key.list
    sudo chown http:http -R /srv/http/pyxpub
    
    
__uWSGI config__
Create: /etc/uwsgi/pyxpub.ini

    [uwsgi]
    socket = /run/uwsgi/%n.sock
    chdir = /srv/http/pyxpub/
    master = true
    plugins = python
    file = xpub.py
    uid = http
    gid = http
    virtualenv = /srv/http/pyxpub/env/
    
__uWSGI start & enable at startup__

    sudo systemctl start uwsgi@pyxpub.service
    sudo systemctl enable uwsgi@pyxpub.service


__setup nginx vhost to reverse proxy uWSGI__

Set up a vhost (preferably with ssl) with following locations and uwsgi_pass:

    upstream _pyxpub {
        server unix:/run/uwsgi/pyxpub.sock;
    }
    
    server {
        server_name pos.devzero.be;
        listen 80;

        root /srv/http/pos.devzero.be/pyxpub;
    
        location / {
                try_files $uri @uwsgi;
        }

        location /embed {
                return 403;
        }

        location @uwsgi {
                include uwsgi_params;
                uwsgi_pass _pyxpub;
        }
    }

__NGINX start & enable at startup__ 

    sudo systemctl start nginx.service
    sudo systemctl enable nginx.service


## Usage
### Direct browser access

    
### JSON
You can also generate a new JSON formatted payment request through the api.

__payment request /api/payment__

Options:
* amount
* label


        curl 'http://localhost:8080/api/payment?amount=0.0023&label=SHOP:1Wed2B44'

        {
        "payment": {
          "amount": "0.0023", 
          "addr": "bitcoincash:qpej4uw429m9m0wawcphw9v4sch2ymd6qsqh7jx9gl", 
          "legacy_addr": "1BVx9uf5UGJDt1eMqjut8qh1K4mmEeDSFQ", 
          "label": "SHOP:1Wed2B44", 
          "qr_img": "/qr?addr=bitcoincash:qpej4uw429m9m0wawcphw9v4sch2ymd6qsqh7jx9gl&amount=0.0023&label=SHOP:1Wed2B44", 
          "payment_uri": "bitcoincash:qpej4uw429m9m0wawcphw9v4sch2ymd6qsqh7jx9gl?amount=0.0023&message=SHOP:1Wed2B44"
          }
        }
        
__payment verification request /api/verify__

Options:
* addr
* amount
or
* label

      curl 'http://localhost:8080/api/verify?addr=bitcoincash:qpemxfnepk9f0g2yzgsyk4ynnklaaunr7g99rrwas9&amount=0.0023'
      
      {"received": 0}
      or 
      {"received": 1}

__payment verification request /api/ledger__

    curl 'http://localhost:8080/api/ledger'
      
      {
       "1":{
          "id":1,
          "timestamp":1519152761.0008476,
          "addr":"bitcoincash:qzwdulf49wfmalj6a36gn2h5ncvrxmw98ydzhxe7gz",
          "amount":"0.00040650",
          "label":"DEVZERO.BE:5cc4f403-9351-42f1-8850-a50735f921fd",
          "received":1,
          "confirmations":0,
          "txid":"5bae0304eb76e78167af30fe6b98f83462828ae974b9c7bc236ebb5b7a9d9e26"
       },
       "2":{
          "id":2,
          "timestamp":1519159704.388939,
          "addr":"bitcoincash:qpej4uw429m9m0wawcphw9v4sch2ymd6qsqh7jx9gl",
          "amount":"0.00976920",
          "label":"DEVZERO.BE:7d2cc3a5-9a6b-4112-b8ac-c60f89d28408",
          "received":0,
          "confirmations":0,
          "txid":"NoTX"
       },
       "3":{
          "id":3,
          "timestamp":1519220076.8360977,
          "addr":"bitcoincash:qpemxfnepk9f0g2yzgsyk4ynnklaaunr7g99rrwas9",
          "amount":"0.0023",
          "label":"SHOP:1Wed2B44",
          "received":0,
          "confirmations":0,
          "txid":"NoTX"
       }
    }


### QR image only

    http://localhost:8080/qr?addr=bitcoincash:qpej4uw429m9m0wawcphw9v4sch2ymd6qsqh7jx9gl&amount=0.0023&label=SHOP:PAYM123


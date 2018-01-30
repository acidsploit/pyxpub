# pyxpub - Private Payment Gateway
 
Pyxpub is a simple selfhosted webapp that displays a webpage with a Bitcoin Cash address and corresponding QR code derived from a pre-defined (Electron Cash) xpub key. It can be accessed directly, be embedded in a webpage through an iframe or be called through a script.

## Introduction
As per Bitcoin best practices it is best to use a new receiving address for each payment request. This for security and privacy implications for both you and your customers or donators. Also, we do not want any private keys on the server generating the receiving address, nor would we want them on any PoS system. This can easily be achieved by using an hd-wallet as described in [BIP32](https://github.com/bitcoin/bips/blob/master/bip-0032.mediawiki). This is the default wallet type when you create a new wallet with [Electron Cash](https://electroncash.org/).

### xpub (Electron Cash)
First, when you create a new wallet with Electron Cash, it is very important to propperly backup and safely store you mnemonic seed. This Electron wallet is your full (send & receive) wallet, make sure it is password protected and also stored safely. You will use it later to retreive payments. The webapp will use the xpub key to generate receive only addresses on the server, corresponding to the addresses from your Electron wallet. This way we don't need private keys on the server. You can find your wallet's master public key or xpub key through the 'Wallet -> Information' menu.

### rate limit by ip
The app is currently rate limited to one unique address per ip address. This is done to prevent snooping and waste of addresses by page reloads if you expose the service publicly (a donation page for example). This is tracked in the ip.list file, generated by the app in the data directory. You can remove this file to erase this history. You can also setup a cron job to do this at whatever interval seems reasonable. The service does not need to be restarted when you remove the ip.list file. (TODO: enable/disable option for rate limiter.)

Keep in mind it is still best to be somewhat conservative with generating new addresses. Since unused addresses will unnecessarily grow your wallet. Because you will have to increase the gap parameter on your full wallet to find new payments, because the addresses having payments in them will have a wider gap between them. If you are not careful you end up with having to generate a whole bunch of addresses of which you only use a few.

## Installation
__clone repo__

    git clone https://github.com/acidsploit/pyxpub.git pyxpub

__create virtualenv and install dependencies__

    cd pyxpub/
    virtualenv env
    source env/bin/activate
    pip install requests
    pip install qrcode
    pip install image
    pip install pycoin
    pip install base58
    pip install cashaddress
    pip install json

__set xpub key__

Copy your xpub key from an Electron Cash wallet and past it in the key.list file.

    touch key.list
    echo 'xpub...' > key.list

__run__

    cd pyxpub/
    source env/bin/activate
    python ./xpub.py

__access locally__

Browse to http://127.0.0.1:8080;


__access though nginx reverse proxy__

Set up a vhost (preferably with ssl) with following locations and proxy_pass:

    # Avoid robots
    location /robots.txt {
        return 200 "User-agent: *\nDisallow: /";
    }

    location  / {
        proxy_pass          http://127.0.0.1:8080;
        proxy_redirect      default;
        proxy_set_header    X-Forwarded-for $proxy_add_x_forwarded_for;
        proxy_set_header    X-Real-IP $remote_addr;
        proxy_set_header    Host $host;
        proxy_set_header    X-Forwarded-Proto $scheme;
        proxy_hide_header   X-Powered-By;
    }

Allow localhost access to port 8080 in your firewall.

    iptables -A INPUT -i lo -p tcp -m tcp --dport 8080 -j ACCEPT


## Usage
### Direct browser access
As noted in the installation instructions, you can access the webapp locally through https://localhost:8080 or directly through the vhost you set up.

__default page__

    https://localhost:8080/
    
![pyxpub example 1](https://i.imgur.com/faDPHsF.png)

__default page with arguments__

    http://localhost:8080/?amount=0.0023&label=SHOP:PAYM123
    
![pyxpub example 2](https://i.imgur.com/vrXDnpZ.png)


Demo: https://donate.devzero.be

    
### JSON
You can also generate a new JSON formatted payment request through the api.

__payment request__

Options:
* amount
* label

        http://localhost:8080/payment?amount=0.0023&label=SHOP:PAYM123

![pyxpub example 4](https://i.imgur.com/vSGGMKg.png)

        curl 'http://localhost:8080/payment?amount=0.0023&label=SHOP:PAYM123'

        {"payment": 
            {"amount": "0.0023", 
             "addr": "bitcoincash:qpej4uw429m9m0wawcphw9v4sch2ymd6qsqh7jx9gl", 
             "label": "SHOP:PAYM123", 
             "qr": "/qr?addr=bitcoincash:qpej4uw429m9m0wawcphw9v4sch2ymd6qsqh7jx9gl&amount=0.0023&label=SHOP:PAYM123"
             }
         }

### QR image only

    http://localhost:8080/qr?addr=bitcoincash:qpej4uw429m9m0wawcphw9v4sch2ymd6qsqh7jx9gl&amount=0.0023&label=SHOP:PAYM123


### Embedded iframe

     <iframe width=100% height=450px frameborder=0 src="https://donate.devzero.be"></iframe> 

Example: https://blog.devzero.be/page/about/ 

# pyxpub
Simple xpub address deriving webapp for Bitcoin Cash.

## Introduction
Pyxpub is a simple webapp that displays a webpage with a Bitcoin Cash address and corresponding qr code derived from an (Electron Cash) xpub key. It can be accessed directly or embedded in a webpage through an iframe.

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

__set xpub key__

Copy your xpub key from an Electron Cash wallet and past it in the key.list file.

    touch key.list
    echo 'xpub...' > key.list

__run__

    cd pyxpub/
    source env/bin/activate
    ./xpub.py

__access locally__

Browse to http://127.0.0.1:8080;


__access though nginx reverse proxy__

Set up a vhost with following locations and proxy_pass:

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
### Direct access
As noted in the installation instructions, you can access the webapp locally through https://localhost:8080 or directly through the vhost you set up.

Example: https://donate.devzero.be

![pyxpub example](https://i.imgur.com/pYYWfWR.png)

### Embedded iframe

     <iframe width=100% height=450px frameborder=0 src="https://donate.devzero.be"></iframe> 

Example: https://blog.devzero.be/page/about/ 

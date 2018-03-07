#!/bin/bash

# sudo apt-get update
# sudo apt-get upgrade
# sudo reboot


UWSGI='''[uwsgi]\n
socket = /run/uwsgi/app/pyxpub/socket\n
processes = 2\n
chdir = /srv/wsgi/pyxpub/\n
master = true\n
plugins = python3\n
file = xpub.py\n
uid = www-data\n
gid = www-data\n
virtualenv = /srv/wsgi/pyxpub/env/\n
'''

NGINX='''upstream _pyxpub {
  server unix:/run/uwsgi/app/pyxpub/socket;
}
 
server {\n
  # server_name yourserver.com;\n
  listen 80 default_server;\n
 \n
  root /srv/http/pyxpub;\n
 \n
  server_name _;\n
 \n
  rewrite ^/$ /react permanent;\n
 \n
  location /react {\n
    index index.html;\n
  }\n
 \n
  location /qr {\n
    try_files $uri @uwsgi;\n
  }\n
 \n
  location /api {\n
    try_files $uri @uwsgi;\n
  }\n
 \n
  location /embed {\n
    return 403;\n
  }\n
 \n
  location @uwsgi {\n
    include uwsgi_params;\n
    uwsgi_pass _pyxpub;\n
  }\n
}\n
'''


echo "Setup System"
apt-get install git vim nginx uwsgi uwsgi-plugin-python3 python-pip python-virtualenv python3-pip python3-virtualenv python3-dev python3-dev python3-setuptools python3-qrcode libjpeg-dev libzlcore-dev libopenjpeg-dev libwebp-dev liblcms2-dev libtiff5-dev libfreetype6-dev libopenjp2-7-dev

mkdir /srv/http/
mkdir /srv/http/pyxpub/

useradd -d /srv/wsgi -M -s /usr/sbin/nologin -U wsgi


echo "Setup pyxpub environment"
cd /srv/wsgi/pyxpub/
virtualenv -p python3 env
source env/bin/activate
pip3 install -r requirements.txt
rm -rf /srv/http/pyxpub/react/
cp -vfr /srv/wsgi/pyxpub/react /srv/http/pyxpub/


echo "Setup uWSGI"
echo -e $UWSGI > /etc/uwsgi/apps-available/pyxpub.ini
rm /etc/uwsgi/apps-enabled/pyxpub.ini
ln -s /etc/uwsgi/apps-available/pyxpub.ini /etc/uwsgi/apps-enabled/pyxpub.ini

find /srv/wsgi/ -type d -exec chown www-data:www-data {} +
find /srv/wsgi/ -type f -exec chown www-data:www-data {} +
find /srv/wsgi/ -type d -exec chmod 755 {} +
find /srv/wsgi/ -type f -exec chmod 644 {} +

systemctl enable uwsgi.service
systemctl restart uwsgi.service
 
 
echo "Setup NGINX"
echo -e $NGINX > /etc/nginx/sites-available/pyxpub.conf
rm /etc/nginx/sites-enabled/pyxpub.conf
ln -s /etc/nginx/sites-available/pyxpub.conf /etc/nginx/sites-enabled/pyxpub.conf
rm /etc/nginx/sites-enabled/default

find /srv/http/ -type d -exec chown www-data:www-data {} +
find /srv/http/ -type f -exec chown www-data:www-data {} +
find /srv/http/ -type d -exec chmod 755 {} +
find /srv/http/ -type f -exec chmod 644 {} +

nginx -t
systemctl enable nginx
systemctl restart nginx

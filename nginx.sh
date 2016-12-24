#!/bin/bash

# Do our cmdline options ------------------------------------------
source optparse.bash
optparse.define short=d long=domain desc="Domain name to listen on, '_' for catchall" variable=DOMAIN
optparse.define short=s long=ssl desc="Do you want a Lets Encrypt SSL Cert" variable=SSL default=false
source $( optparse.build )

# ASSUMPTIONS:
# - A standard /etc/nginx installation
# - A standard nginx/sites-available nginx/sites-enabled configuration
# - Logging into /var/log/nginx
# - Webroot in /srv/www
#   - If its not there. :%s/\/srv\/www/<whatever>/g for the templates and this
# - a default webdir with the index.html and robots.txt you normally use.
#   - /srv/www/default/index.html
#   - /srv/www/default/robots.txt
if [ "$DOMAIN" == "" ]; then
    usage
    exit 0
fi

# Check if NGINX is installed
if ! which nginx > /dev/null 2>&1; then
    sudo apt-get update
    sudo apt-get install nginx
fi

if [ "$DOMAIN" == '_' ]; then
    DOMAIN="catchall"
    TEMPLATE_PREFIX="catchall_"
else
    TEMPLATE_PREFIX=""
fi

echo "Creating files for $DOMAIN"
if [ ! -d /var/log/nginx/$DOMAIN ]; then
    echo "Creating log files"
    sudo mkdir /var/log/nginx/$DOMAIN
    sudo touch /var/log/nginx/$DOMAIN/error.log
    sudo touch /var/log/nginx/$DOMAIN/access.log
fi

if [ ! -d /srv/www ]; then
    echo "Creating parent /srv/www/ directory"
    sudo mkdir /srv/www
    sudo chown -R www-data:www-data /srv/www
fi

if [ ! -d /srv/www/default ]; then
    echo "Creating default directory"
    sudo mkdir /srv/www/default
    echo "hello" | sudo tee /srv/www/default/index.html
    sudo touch /srv/www/default/robots.txt
    sudo chown -R www-data:www-data /srv/www/default
fi

if [ ! -d /srv/www/$DOMAIN ]; then
    echo "Creating webroot directory"
    sudo mkdir /srv/www/$DOMAIN
    sudo chown www-data:www-data /srv/www/$DOMAIN
    sudo ln -s /srv/www/default/index.html /srv/www/$DOMAIN/index.html
    sudo ln -s /srv/www/default/robots.txt /srv/www/$DOMAIN/robots.txt
    sudo chown -R www-data:www-data /srv/www/$DOMAIN
fi

if [ -e /etc/nginx/sites-available/$DOMAIN ]; then
    echo "Backing up current NGINX configuration"
    sudo cp /etc/nginx/sites-available/$DOMAIN /etc/nginx/sites-available/$DOMAIN.bak
fi

echo "Creating nginx config"
sudo cat templates/"$TEMPLATE_PREFIX"nginx_no_ssl | sed "s/template/$DOMAIN/g" > /etc/nginx/sites-available/$DOMAIN
sudo nginx -t && sudo service nginx reload

if [ ! -e /etc/nginx/sites-enabled/$DOMAIN ]; then
    echo "Symlinking nginx"
    sudo ln -s /etc/nginx/sites-available/$DOMAIN /etc/nginx/sites-enabled/$DOMAIN;
    sudo service nginx reload
fi

if [ "$SSL" == "true" ]; then
    echo "LetsEncrypting SSL Cert"
    chmod +x certbot-auto
    ./certbot-auto certonly --agree-tos --webroot -w /srv/www/$DOMAIN/ -d $DOMAIN -d www.$DOMAIN

    sudo cat templates/"$TEMPLATE_PREFIX"nginx_with_ssl | sed "s/template/$DOMAIN/g" > /etc/nginx/sites-available/$DOMAIN

    if [ ! -e /etc/nginx/dhparam.pem ]; then
        echo "Generating DH Param for better SSL Security. Will take a while"
        openssl dhparam -out /etc/nginx/dhparam.pem 4096
    fi

    sudo nginx -t && sudo service nginx reload
else
    echo "SSL Not selected, please rerun with ./create $DOMAIN 1"
    exit 0;
fi



#!/bin/bash

# Do our cmdline options ------------------------------------------
source optparse.bash
optparse.define short=d long=domain desc="Domain name to listen on, '_' for catchall" variable=DOMAIN
optparse.define short=a long=app desc="Folder the app is in. so given myapp, looking for sth structured like myapp/__init__.py" variable=APP
source $( optparse.build )
# -----------------------------------------------------------------

# Check your inputs
if [ "$DOMAIN" == "" ]; then
    usage
    exit 0
fi

if [ "$APP" == "" ]; then
    usage
    exit 0
fi

if [ ! -d "$APP" ]; then
    echo "App folder not found"
    usage
    exit 0
fi

# This script relies on nginx being installed and configured already.
if [ ! -e /etc/nginx/sites-available/$DOMAIN ]; then
    echo "The domain '$DOMAIN' does not have an nginx entry."
    echo "Please run nginx.sh first"
    exit 0
fi

if [ "$DOMAIN" == '_' ]; then
    DOMAIN="catchall"
    TEMPLATE_PREFIX="catchall_"
else
    TEMPLATE_PREFIX=""
fi

# Lets check if our uwsgi dependencies exist yet
DEPENDENCIES=""

if ! which virtualenv > /dev/null 2>&1; then
    DEPENDENCIES="$DEPENDENCIES python3 python3-dev python3-pip python3-dev python3-virtualenv virtualenv"
fi

if ! which uwsgi > /dev/null 2>&1; then
    echo "Uwsgi missing. Adding to install list"
    DEPENDENCIES="$DEPENDENCIES uwsgi uwsgi-emperor uwsgi-plugin-python3"
fi

if [ ! "$DEPENDENCIES" == "" ]; then
    sudo apt-get update
    sudo apt-get install $DEPENDENCIES
fi

# Set up the uwsgi files
if [ -e "/srv/www/$DOMAIN/app_uwsgi.ini" ]; then
    echo "app_uwsgi.ini exists in /srv/www/$DOMAIN/. backing up"
    mv "/srv/www/$DOMAIN/app_uwsgi.ini" "/srv/www/$DOMAIN/app_uwsgi.ini.bak"
fi

echo "Creating app_uwsgi.ini"
cat templates/app_uwsgi.ini | sed "s/#domain#/$DOMAIN/g" > "/srv/www/$DOMAIN/app_uwsgi.ini"
sudo chown www-data:www-data "/srv/www/$DOMAIN/app_uwsgi.ini"
sudo ln -s "/srv/www/$DOMAIN/app_uwsgi.ini" "/etc/uwsgi-emperor/vassals/$DOMAIN.ini"

if [ ! -e "/etc/systemd/system/emperor.uwsgi.service" ]; then
    echo "emperor uwsgi systemd service does not exist. making it now"
    echo "You will be able to use it as \`sudo service emperor.uwsgi [start|stop|status]\`"
    cp templates/emperor.uwsgi.service /etc/systemd/system/emperor.uwsgi.service
fi

if [ ! -d "/var/log/uwsgi/$DOMAIN/" ]; then
    mkdir /var/log/uwsgi/$DOMAIN
    chown -R www-data:www-data "/var/log/uwsgi/$DOMAIN"
fi

# Fix up your nginx config
if [ -e "/etc/nginx/sites-available/$DOMAIN" ]; then
    echo "Backing up current NGINX configuration"
    sudo cp "/etc/nginx/sites-available/$DOMAIN" "/etc/nginx/sites-available/$DOMAIN.bak"
fi

# I know this is fucking disgusting. To explain the steps
# Reverse the file.
# Replace the last occurence with our config for the flask app
# - This is a hack to let us replace the last occurence of }
#   (usually the end of the nginx config for that server)
# The config is a subshell that escapes special bash characters [$@/] and replaces the newlines with \n
# re-reverse the file
# Then replace our #domain# tag with the domain and spit it back out
cat "/etc/nginx/sites-available/$DOMAIN" | tac | perl -0777 -pe "s/(.*)}/\$1}\n`tac templates/uwsgi-nginx.conf | perl -pne 's/([\/\\$\@])/\\\\$1/g' | perl -pne 's/\n$/\\n/g'`/" | tac | sed "s/#domain#/$DOMAIN/" > /tmp/$DOMAIN
mv /tmp/$DOMAIN "/etc/nginx/sites-available/$DOMAIN"

# Copy our app across to the target folder.
if [ -d  "/srv/www/$DOMAIN/flaskr" ]; then
    echo "App folder already exists at destination. moving out of the way"
    mv "/srv/www/$DOMAIN/flaskr" "/srv/www/$DOMAIN/flaskr.old"
fi

cp -rv "$APP" "/srv/www/$DOMAIN/flaskr"

# Do our PIP dependencies
echo "Installing pip dependencies into virtual env at /srv/www/$DOMAIN"
cd "/srv/www/$DOMAIN"
virtualenv -p /usr/bin/python3 /srv/www/$DOMAIN/env
"/srv/www/$DOMAIN/env/bin/pip3" install flask

echo "Done. Restarting NGINX and uwsgi-emperor. Good Luck!"
sudo service emperor.uwsgi restart
sudo service nginx restart




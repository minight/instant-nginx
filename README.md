# instant-nginx

here's a few tools I made to help me bootstrap nginx faster.

## nginx.sh

Lets you instantly create an nginx config for a website. Even if you have nothing installed on the server

If you use the `-s true` switch, then you'll also do letsencrypt for that domain name.

The script uses certbot-auto from the (letsencrypt repo)[https://github.com/certbot/certbot]

### Uses:
- Heaps good if you want to instantly create a letsencrypt ssl cert when you have nginx.

## flask.sh

I got sick of figuring out how to use uwsgi with flask. So i made a script to make it faster.

It leverages the configs and setup of `nginx.sh` so do that first. then use this on the same domain

Look at the example app folder for how you should structure your app. You can do whatever you want. as long as its an importable folder/module


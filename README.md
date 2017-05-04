# instant-nginx 0.2.0

here's a few tools i made to deploy flask apps really fast

## nginx.py

Lets you instantly create an nginx config for a website. Even if you have nothing installed on the server

*USES PYTHON3*

_Usage_
```
sudo python3 nginx.py <domain> <ssl>
  <domain> (optional) - if none, defaults to catchall
  <ssl> (optional) - true|false - letsencrypt ssl

```

The script uses certbot-auto from the [letsencrypt repo](https://github.com/certbot/certbot)

## flask.py

I got sick of figuring out how to use uwsgi with flask. So i made a script to make it faster.

run nginx.py first since you needa a prepared nginx config and a running nginx server

just follow the included template app

## Acknolwedgements

[letsencrypt](https://github.com/certbot/certbot) - Lets encrypt is awesome

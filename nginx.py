#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import pathlib
import datetime
import pwd


def usage():
    print("""sudo python nginx.py <domain> <ssl>
<domain> (optional) - if none, defaults to catchall
<ssl> (optional) - true|false - letsencrypt ssl""")
    exit(0)


def chown(f, user):
    gid = pwd.getpwnam(user).pw_gid
    uid = pwd.getpwnam(user).pw_uid
    os.chown(f, uid, gid)


def create_and_chown(path, name):
    if not os.path.exists(path):
        if path.endswith('/'):
            os.makedirs(path)
        else:
            pathlib.Path(path).touch()
    chown(path, name)


def init_domain(domain, ssl=False):
    if not os.path.exists("/etc/nginx/"):
        os.system("apt-get install -y nginx")

    # Create default files
    create_and_chown('/srv/www/', 'www-data')
    create_and_chown('/srv/www/default/', 'www-data')

    # Create default files
    default_index = '/srv/www/default/index.html'
    if not os.path.exists(default_index):
        open(default_index, 'w+').write('hello')
        chown(default_index, 'www-data')

    default_robots = '/srv/www/default/robots.txt'
    if not os.path.exists(default_robots):
        open(default_robots, 'w+').write('')
        chown(default_robots, 'www-data')

    # Create domain files
    if domain:
        domain_root = os.path.join('/srv/www/', domain, '')
        create_and_chown(domain_root, 'www-data')

        domain_index = os.path.join(domain_root, 'index.html')
        domain_robots = os.path.join(domain_root, 'robots.txt')

        try:
            os.symlink(default_index, domain_index)
            os.symlink(default_robots, domain_robots)
        except Exception as e:
            print(
                "[!] Probably tried to write over existing symlink for default files. Not doing it\n\t",
                e)
            pass

        # check if our log files exist
        log_dir = os.path.join('/var/log/nginx', domain, '')
        create_and_chown(log_dir, 'www-data')

        error_file = os.path.join(log_dir, 'error.log')
        create_and_chown(error_file, 'www-data')

        access_file = os.path.join(log_dir, 'access.log')
        create_and_chown(access_file, 'www-data')

    # Create NGINX Config
    if domain == 'default':  # We want a catchall default route
        config_data = open('./templates/nginx_default').read()
    else:  # user specified a domain so we'll set that up for them
        config_data = open('./templates/nginx_domain').read().replace(
            'repl_domain', domain)

    nginx_config = os.path.join('/etc/nginx/sites-available', domain)
    if os.path.exists(nginx_config):
        new_name = nginx_config + str(datetime.datetime.now()).replace(' ',
                                                                        '_')
        print(
            "[!] Found an existing nginx config at {0}. Backing up to {1}".
            format(nginx_config, new_name))
        os.rename(nginx_config, new_name)

    open(nginx_config, 'w+').write(config_data)

    nginx_enabled_config = os.path.join('/etc/nginx/sites-enabled', domain)
    if not os.path.exists(nginx_enabled_config):
        os.symlinK(nginx_config, nginx_enabled_config)

    # Start nginx
    os.system("service nginx start")
    if os.system("service nginx restart"):
        print("[!] Oh no. nginx failed to start. Aborting")
        exit(-1)

    print("[+] Successfully created nginx stuff for {0}".format(
        domain if domain else 'default'))

    print("[+] Now doing Letsencrypt")

    if ssl:
        os.system("./certbot-auto certonly --agree-tos --webroot -w /srv/www/{domain}/ -d {domain}".format(domain = domain))
        nginx_content = open(nginx_config, 'r').read()
        ssl_template = open('./templates/ssl_snippet').read().replace("template", domain)
        if '#ssl' in nginx_content:
            nginx_content = open(nginx_config, 'r').read().replace('#ssl', ssl_template)
        else:
            print("[!] Seems please add #ssl into the nginx config where you would like to add the ssl stuff")
            print("[!] Your file to edit: ", nginx_config)
            print("[!] Then run this again")
            exit(-1)

        open(nginx_config, 'w').write(nginx_content)

        if not os.path.exists("/etc/nginx/dhparam.pem"):
            print("[!] Generating DH Param for better SSL Security. Will take a while")
            os.system("openssl dhparam -out /etc/nginx/dhparam.pem 4096")

        if os.system("service nginx restart"):
            print("[!] Oh no. nginx failed to start.")
            os.system("nginx -t")
            exit(-1)

if __name__ == "__main__":
    domain = 'default'
    ssl = False
    help_words = ['-h', 'h', 'help', '?']
    if len(sys.argv) > 1:
        if sys.argv[1] in help_words:
            usage()
            exit(0)

        domain = sys.argv[1]
        if len(sys.argv) > 2:
            ssl = sys.argv[2]

    os.system("apt-get update")
    init_domain(domain, ssl)

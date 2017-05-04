#!/usr/bin/env python3
from __future__ import print_function
import os
import shutil
import sys


def usage():
    print("""sudo python flask.py <domain_name>
domain_name (optional):
    what domain name the nginx folder is installed under
          """)

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

def init_flask(domain):
    print("[+] Trying to set up flask for domain:", domain)
    if not os.path.exists("/etc/uwsgi/"):
        os.system("apt-get install -y uwsgi")

    os.system("apt-get install -y uwsgi-plugin-python3")

    if os.system("pip3"):
        print("[+] Installing python3-pip")
        os.system("apt-get install -y python3-pip")

    if os.system("virtualenv") != 2:
        print("[+] Installing virtualenv")
        os.system("pip3 install virtualenv")

    # move the flask app
    flask_path = os.path.join("/srv/www/", domain, "app")
    if not os.path.exists(flask_path):
        print("[+] Copying the flask app across")
        shutil.copytree('./app', flask_path)
        os.system("chown -R www-data:www-data {}".format(flask_path))

    # get the venv ready
    venv_path = os.path.join(flask_path, 'env')
    if not os.path.exists(venv_path):
        os.system("virtualenv {venv}".format(venv = venv_path))

    venv_pip = os.path.join(flask_path, 'env', 'bin/pip3')
    req_file = os.path.join(flask_path, 'requirements.txt')
    if os.system("{venv} install -r {req}".format(
            venv=venv_pip, req=req_file)):
        print("[!] Something went wrong installing the requirements. Aborting")
        exit(-1)

    # get the logging files ready
    log_dir = "/var/log/uwsgi/app/"
    if not os.path.exists(log_dir):
        create_and_chown(log_dir, 'www-data')

    # get the uwsgi file ready
    uwsgi_file = os.path.join(flask_path, 'uwsgi.ini')

    # update the uwsgi file with the domain
    uwsgi_contents = open(uwsgi_file, 'r').read().replace('repl_domain', domain)
    open(uwsgi_file, 'w').write(uwsgi_contents)

    # symlink it in
    uwsgi_path = os.path.join("/etc/uwsgi/apps-enabled/", "{0}.ini".format(domain))
    if os.path.exists(uwsgi_path):
        print("[!] There already exists a uwsgi ini ({}) in the uwsgi/apps-enabled directory. Please remove and run this script again".format(uwsgi_path))
        resp = input("[!] Do you wish to overwrite this file? [y/n]")
        while resp not in 'yn':
            resp = input("[!] Do you wish to overwrite this file? [y/n]")
        if resp == 'n':
            print('[!] Aborting at user request')
            exit(-1)
        else:
            os.remove(uwsgi_path)

    try:
        os.symlink(uwsgi_file, uwsgi_path)
    except Exception as e:
        print("[!] Something went very wrong\n", e)
        exit(-1)

    # edit the nginx config
    nginx_flask_snippet = open('./templates/flask_snippet', 'r').read().replace("repl_domain", domain)
    nginx_file = os.path.join("/etc/nginx/sites-enabled/", domain)
    nginx_config = open(nginx_file, 'r').read()

    if '#uwsgi' in nginx_config:
        nginx_config = nginx_config.replace("#uwsgi", nginx_flask_snippet)
    else:
        print("[!] Seems please add #uwsgi into the nginx config where you would like to add the uwsgi stuff")
        print("[!] Your file to edit: ", nginx_file)
        print("[!] Then run this again")
        exit(-1)

    open(nginx_file, 'w').write(nginx_config)

    os.system("service uwsgi start")
    if os.system("service uwsgi restart"):
        print("[!] Failed to restart uwsgi... not sure why")
        exit(-1)

    if os.system("service nginx restart"):
        print("[!] Failed to restart nginx... not sure why")
        exit(-1)

    print("[!] New app installed")


if __name__ == "__main__":
    domain = 'default'
    ssl = None
    help_words = ['-h', 'h', 'help', '?']
    if len(sys.argv) > 1:
        if sys.argv[1] in help_words:
            usage()
            exit(0)

        domain = sys.argv[1]

    os.system("apt-get update")
    init_flask(domain)

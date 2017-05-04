from flask import Flask

class ConfigClass(object):
    DEBUG = True

app = Flask(__name__)
app.config.from_object(__name__ + '.ConfigClass')

from . import models

from .basic import app as basic_bp
app.register_blueprint(basic_bp)

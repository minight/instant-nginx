from flask import Blueprint

app = Blueprint(
    'basic',
    __name__,
    template_folder='template',
    static_folder='static')

from . import views


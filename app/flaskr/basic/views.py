from flask import render_template_string, request
import re
from . import app

@app.route('/')
def home():
    if re.match(r'[Cc]url.*',request.headers.get('User-Agent')):
        return render_template_string("you are curl")

    return render_template_string("hello")

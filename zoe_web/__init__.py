from datetime import datetime

from flask import Flask, url_for
from zoe_web.api import api_bp
from zoe_web.web import web_bp

app = Flask(__name__, static_url_path='/does-not-exist')
app.register_blueprint(web_bp, url_prefix='')
app.register_blueprint(api_bp, url_prefix='/api')

app.secret_key = b"\xc3\xb0\xa7\xff\x8fH'\xf7m\x1c\xa2\x92F\x1d\xdcz\x05\xe6CJN5\x83!"

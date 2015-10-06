__author__ = 'erikfarmer'

from flask import Flask
from views import api

from common.models.db import db


app = Flask(__name__, template_folder='templates', static_folder='static')
app.config.from_object('widget_service.config')
app.register_blueprint(api.mod, url_prefix='/widget')

db.init_app(app)
db.app = app

__author__ = 'erikfarmer'

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

import config


app = Flask(__name__, template_folder='templates', static_folder='static')
app.config.from_object(config)

db = SQLAlchemy(app)
from .views import api

app.register_blueprint(api.mod, url_prefix='/v1')

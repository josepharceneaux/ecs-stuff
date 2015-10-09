__author__ = 'erikfarmer'

from flask import Flask
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__, template_folder='templates', static_folder='static')
app.config.from_object('widget_service.config')

db = SQLAlchemy(app)
from .views import api

app.register_blueprint(api.mod, url_prefix='/widget/v1')

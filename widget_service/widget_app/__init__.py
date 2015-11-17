__author__ = 'erikfarmer'

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from healthcheck  import HealthCheck
import config


app = Flask(__name__, template_folder='templates', static_folder='static')
app.config.from_object(config)

db = SQLAlchemy(app)
from .views import api

# wrap the flask app and give a heathcheck url
health = HealthCheck(app, "/healthcheck")

app.register_blueprint(api.mod, url_prefix='/v1')

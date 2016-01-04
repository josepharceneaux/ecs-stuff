__author__ = 'erikfarmer'

from flask import Flask
from healthcheck  import HealthCheck
import config
from widget_service.common.models.db import db


app = Flask(__name__, template_folder='templates', static_folder='static')
app.config.from_object(config)

db.init_app(app)
db.app = app
from .views import api

# wrap the flask app and give a heathcheck url
health = HealthCheck(app, "/healthcheck")

app.register_blueprint(api.mod, url_prefix='/v1')

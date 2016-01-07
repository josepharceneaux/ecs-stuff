
__author__ = 'erikfarmer'

import config
from flask import Flask
from healthcheck import HealthCheck
from widget_service.common.models.db import db
from flask.ext.common.common.routes import WidgetApi, HEALTH_CHECK

app = Flask(__name__, template_folder='templates', static_folder='static')
app.config.from_object(config)

db.init_app(app)
db.app = app
from .views import api

# wrap the flask app and give a heathcheck url
health = HealthCheck(app, HEALTH_CHECK)

app.register_blueprint(api.mod, url_prefix=WidgetApi.URL_PREFIX)

__author__ = 'erikfarmer'

import config
from flask import Flask
from flask.ext.cors import CORS
from healthcheck import HealthCheck
from widget_service.common.models.db import db
from widget_service.common.routes import WidgetApi, HEALTH_CHECK
from widget_service.common.talent_config_manager import load_gettalent_config, TalentConfigKeys

app = Flask(__name__, template_folder='templates', static_folder='static')
app.config.from_object(config)  # Widget service has its own config as well
load_gettalent_config(app.config)
logger = app.config[TalentConfigKeys.LOGGER]

db.init_app(app)
db.app = app
from .views import api

# Enable CORS for all origins & endpoints
CORS(app, resources={r"*": {"origins": [r"*.gettalent.com", "http://localhost"]}})

# wrap the flask app and give a heathcheck url
health = HealthCheck(app, HEALTH_CHECK)

app.register_blueprint(api.mod, url_prefix=WidgetApi.URL_PREFIX)

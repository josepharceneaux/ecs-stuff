__author__ = 'erikfarmer'

import config
from flask import Flask, render_template
from flask.ext.cors import CORS
from healthcheck import HealthCheck
from widget_service.common.models.db import db
from widget_service.common.routes import WidgetApi, HEALTH_CHECK, GTApis
from widget_service.common.talent_config_manager import load_gettalent_config, TalentConfigKeys
from widget_service.common.talent_flask import TalentFlask


app = Flask(__name__, static_folder='static')
app.config.from_object(config)  # Widget service has its own config as well
load_gettalent_config(app.config)
logger = app.config[TalentConfigKeys.LOGGER]

db.init_app(app)
db.app = app
from .views import api


# Enable CORS for *.gettalent.com and localhost
CORS(app, resources=GTApis.CORS_HEADERS)

# wrap the flask app and give a heathcheck url
health = HealthCheck(app, HEALTH_CHECK)

app.register_blueprint(api.mod, url_prefix=WidgetApi.URL_PREFIX)

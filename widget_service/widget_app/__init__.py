__author__ = 'erikfarmer'

from flask import Flask

from common.models.db import db
import config


app = Flask(__name__, template_folder='templates', static_folder='static')
app.config.from_object(config)

db.init_app(app)
db.app = app
from .views import api

app.register_blueprint(api.mod, url_prefix='/v1')

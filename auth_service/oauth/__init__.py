__author__ = 'ufarooqi'

from flask import Flask
from flask_oauthlib.provider import OAuth2Provider
from common.models.db import db

app = Flask(__name__)
app.config.from_object('auth_service.config')

logger = app.config['LOGGER']
from auth_service.common.error_handling import register_error_handlers
register_error_handlers(app, logger)

db.init_app(app)
db.app = app

gt_oauth = OAuth2Provider()
gt_oauth.init_app(app)

import views

db.create_all()
db.session.commit()

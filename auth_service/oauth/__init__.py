__author__ = 'ufarooqi'

from flask import Flask
from flask_oauthlib.provider import OAuth2Provider
from auth_service.models.db import db

app = Flask(__name__)

gt_oauth = OAuth2Provider()
app.config.from_object('auth_service.config')
logger = app.config['LOGGER']

db.init_app(app)
db.app = app

gt_oauth.init_app(app)

import views

db.create_all()
db.session.commit()


__author__ = 'ufarooqi'

from flask import Flask
from flask_oauthlib.provider import OAuth2Provider
from models import db

app = Flask(__name__)

gt_oauth = OAuth2Provider()
app.config.from_object('auth_service.config')
logger = app.config['LOGGER']

db.init_app(app)
db.app = app

db.metadata.reflect(db.engine, only=['user'])

gt_oauth.init_app(app)

from auth_service.oauth import views

db.create_all()
db.session.commit()


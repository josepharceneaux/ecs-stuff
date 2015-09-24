__author__ = 'ufarooqi'

from flask import Flask
from flask_oauthlib.provider import OAuth2Provider
from flask.ext.sqlalchemy import SQLAlchemy

app = Flask(__name__)

gt_oauth = OAuth2Provider()
app.config.from_object('config')
logger = app.config['LOGGER']

db = SQLAlchemy(app)
db.metadata.reflect(db.engine, only=['user'])

gt_oauth.init_app(app)

from oauth import models
from oauth import views

db.create_all()
db.session.commit()


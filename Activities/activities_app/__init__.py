__author__ = 'Erik Farmer'

from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config.from_object('config')
db = SQLAlchemy(app)
db.metadata.reflect(db.engine, only=['user', 'activity', 'client', 'token'])

from activities_app.views import api
app.register_blueprint(api.mod)
"""Initializer for activities_app"""
__author__ = 'Erik Farmer'

from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config.from_object('activities_service.config')
db = SQLAlchemy(app)
db.metadata.reflect(db.engine, only=['activity', 'candidate', 'client', 'domain', 'token', 'user'])

from activities_service.activities_app.views import api
app.register_blueprint(api.mod)

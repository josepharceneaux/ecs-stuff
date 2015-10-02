"""Initializer for activities_app"""
__author__ = 'Erik Farmer'

from flask import Flask
from activities_service.models.db import db
from activities_service.activities_app.views import api

app = Flask(__name__)
app.config.from_object('activities_service.config')
app.register_blueprint(api.mod)

db.init_app(app)
db.app = app

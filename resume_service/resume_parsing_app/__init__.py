"""Initializer for Resume Parsing App"""
__author__ = 'erikfarmer'

from flask import Flask
from views import api
from resume_service.models.db import db
from resume_service.models.candidate import *
from resume_service.models.user import *

app = Flask(__name__)
app.config.from_object('resume_service.config')
app.register_blueprint(api.mod)

db.init_app(app)
db.app = app

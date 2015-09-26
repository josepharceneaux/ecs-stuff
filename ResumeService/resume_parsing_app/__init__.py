"""Initializer for Resume Parsing App"""
__author__ = 'erikfarmer'

from flask import Flask


app = Flask(__name__)
app.config.from_object('config')

from resume_parsing_app.views import api
app.register_blueprint(api.mod)

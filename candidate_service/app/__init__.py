from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import logging

app = Flask(__name__)

db = SQLAlchemy(app)


logger = logging.basicConfig(filename='error.log', level=logging.DEBUG)

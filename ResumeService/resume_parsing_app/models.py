__author__ = 'erik-farmer'

from flask.ext.sqlalchemy import SQLAlchemy

from . import app

db = SQLAlchemy(app)
db.metadata.reflect(db.engine)
db.init_app(app)


class User(db.Model):
    __table__ = db.Model.metadata.tables['user']


class Client(db.Model):
    __table__ = db.Model.metadata.tables['client']


class Token(db.Model):
    __table__ = db.Model.metadata.tables['token']

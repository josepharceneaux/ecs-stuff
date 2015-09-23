__author__ = 'Erik Farmer'

from activities_app import db


class User(db.Model):
    __table__ = db.Model.metadata.tables['user']


class Activity(db.Model):
    __table__ = db.Model.metadata.tables['activity']


class Client(db.Model):
    __table__ = db.Model.metadata.tables['client']


class Token(db.Model):
    __table__ = db.Model.metadata.tables['token']

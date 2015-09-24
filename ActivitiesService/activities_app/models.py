"""Model definitions for tables used in ActivityService"""

__author__ = 'Erik Farmer'

from activities_app import db


class Activity(db.Model):
    __table__ = db.Model.metadata.tables['activity']


class Candidate(db.Model):
    __table__ = db.Model.metadata.tables['candidate']


class Client(db.Model):
    __table__ = db.Model.metadata.tables['client']


class Domain(db.Model):
    __table__ = db.Model.metadata.tables['domain']


class Token(db.Model):
    __table__ = db.Model.metadata.tables['token']


class User(db.Model):
    __table__ = db.Model.metadata.tables['user']

"""Initializer for Social Network Service App"""
from types import MethodType

__author__ = 'zohaib'

from flask import Flask
from common.models.db import db

app = Flask(__name__)
app.config.from_object('social_network_service.config')
logger = app.config['LOGGER']
# app.config.from_object(__name__)


db.init_app(app)
db.app = app


def to_json(self):
    """
    Converts SqlAlchemy object to serializable dictionary
    """
    from social_network_service.utilities import camel_case_to_snake_case
    # add your coversions for things like datetime's
    # and what-not that aren't serializable.
    convert = dict(DATETIME=str)

    data = dict()
    for col in self.__class__.__table__.columns:
        name = camel_case_to_snake_case(col.name)
        value = getattr(self, name)
        typ = str(col.type)
        if typ in convert.keys() and value is not None:
            try:
                data[name] = convert[typ](value)
            except Exception as e:
                data[name] = "Error:  Failed to covert using ", str(convert[typ])
        elif value is None:
            data[name] = str()
        else:
            data[name] = value
    return data
db.Model.to_json = MethodType(to_json, None, db.Model)

# from common.error_handling import register_error_handlers
# register_error_handlers(app, logger)

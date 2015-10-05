"""Initializer for Social Network Service App"""
from types import MethodType

__author__ = 'zohaib'

from flask import Flask
from common.models.db import db

flask_app = Flask(__name__)
flask_app.config.from_object('social_network_service.config')
logger = flask_app.config['LOGGER']


db.init_app(flask_app)
db.app = flask_app


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


def save(self):
    """
    This method allows a model instance to save itself in database by calling save
    e.g.
    event = Event(**kwargs)
    event.save()
    :return: same model instance
    """
    db.session.add(self)
    db.session.commit()
    return self


def update(self, **data):
    """
    This method allows a model instance to save itself in database by calling save
    e.g.
    event = Event(**kwargs)
    event.save()
    :return: same model instance
    """
    self.query.filter_by(id=self.id).update(data)
    db.session.commit()
    return self

@classmethod
def get_by_id(cls, _id):
    try:
        obj = cls.query.get(_id)
    except:
        return None
    return obj


db.Model.to_json = MethodType(to_json, None, db.Model)
db.Model.save = MethodType(save, None, db.Model)
db.Model.update = MethodType(update, None, db.Model)
db.Model.get_by_id = get_by_id

# from common.error_handling import register_error_handlers
# register_error_handlers(app, logger)

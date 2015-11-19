"""Utility functions related to database/model code."""
__author__ = 'erikfarmer'

from sqlalchemy.sql.expression import ClauseElement


def get_or_create(session, model, defaults=None, **kwargs):
    """ Fetches or makes a db object depending on kwarg filters.
    :param session: (SQLAlchemy db session object) Session typically passed in as db.session.
    :param model: (SQLAlchemy model object) The table to be queried/model object to be returned.
    :param defaults: (dict) Fields to be updated during object creation.
    :param kwargs: (dict) Query filter parameters.
    :return: (tuple) Tuple containing a db object and a boolean (True if object was created, False
                     if found in db). Session will need to be committed on a 'created = True'
    """
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance, False
    else:
        params = dict((k, v) for k, v in kwargs.iteritems() if not isinstance(v, ClauseElement))
        params.update(defaults or {})
        instance = model(**params)
        session.add(instance)
        return instance, True


def serialize_queried_sa_obj(obj):
    """Converts a SQLAlchemy model object into a python standard dictionary.
    :param obj: (SQLAlchemy model object) The model object to be serialized.
    :return: (dict) Dictionary representing the model object that was passed.
    """
    attrs = vars(obj)
    attrs.pop('_sa_instance_state', None)
    return attrs
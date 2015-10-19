"""Utility functions related to database/model code."""
__author__ = 'erikfarmer'

from sqlalchemy.sql.expression import ClauseElement


def get_or_create(session, model, defaults=None, **kwargs):
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
    attrs = vars(obj)
    attrs.pop('_sa_instance_state', None)
    return attrs
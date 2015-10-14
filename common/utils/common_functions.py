from sqlalchemy.sql.expression import ClauseElement
from activity_service.common.models.db import db
from activity_service.activities_app import app
from flask import current_app

# Setting current app context
with app.app_context():
    db.session.commit()
    print "current running app: %s" % current_app.name


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

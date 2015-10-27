from sqlalchemy.sql.expression import ClauseElement
from activity_service.common.models.db import db
from activity_service.activities_app import app
from flask import current_app


# Setting current app context
with app.app_context():
    db.session.commit()
    print "current running app: %s" % current_app.name

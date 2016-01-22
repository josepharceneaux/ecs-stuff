from models import (
    associations,
    candidate,
    candidate_edit,
    email_marketing,
    event,
    event_organizer,
    language,
    misc,
    rsvp,
    smartlist,
    talent_pools_pipelines,
    university,
    user,
    venue,
    widget
)

from models.db import db


def db_create_all():

    db.create_all()
    db.session.commit()
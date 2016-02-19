from models import (
    associations,
    candidate,
    candidate_edit,
    email_campaign,
    event,
    event_organizer,
    language,
    misc,
    rsvp,
    smartlist,
    sms_campaign,
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
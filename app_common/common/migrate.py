from models.db import db


def db_create_all():

    db.create_all()
    db.session.commit()
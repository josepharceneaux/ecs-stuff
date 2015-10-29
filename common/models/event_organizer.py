from db import db
import event


class EventOrganizer(db.Model):
    __tablename__ = 'event_organizer'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column('userId', db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column('name', db.String(200))
    email = db.Column('email', db.String(200))
    about = db.Column('about', db.String(1000))

    event = db.relationship('Event', backref='event_organizer', lazy='dynamic')

    @classmethod
    def get_by_user_id(cls, user_id):
        assert user_id
        return cls.query.filter(EventOrganizer.user_id == user_id).all()

    @classmethod
    def get_by_user_id_organizer_id(cls, user_id, organizer_id):
        assert user_id
        return cls.query.filter(EventOrganizer.user_id == user_id,
                                EventOrganizer.id == organizer_id).first()

    @classmethod
    def get_by_user_id_and_name(cls, user_id, name):
        assert user_id and name
        return cls.query.filter(EventOrganizer.user_id == user_id,
                                EventOrganizer.name == name).first()

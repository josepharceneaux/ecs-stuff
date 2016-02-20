from db import db
import event


class EventOrganizer(db.Model):
    __tablename__ = 'event_organizer'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column('userId', db.BIGINT, db.ForeignKey('user.Id'), nullable=False)
    name = db.Column(db.String(200))
    email = db.Column(db.String(200))
    about = db.Column(db.String(1000))

    # Relationships
    event = db.relationship('Event', backref='event_organizer', lazy='dynamic')

    @classmethod
    def get_by_user_id(cls, user_id):
        assert isinstance(user_id, (int, long))
        return cls.query.filter(EventOrganizer.user_id == user_id).all()

    @classmethod
    def get_by_user_id_organizer_id(cls, user_id, organizer_id):
        assert isinstance(user_id, (int, long))
        return cls.query.filter(EventOrganizer.user_id == user_id,
                                EventOrganizer.id == organizer_id).first()

    @classmethod
    def get_by_user_id_and_name(cls, user_id, name):
        assert isinstance(user_id, (int, long))
        return cls.query.filter(EventOrganizer.user_id == user_id,
                                EventOrganizer.name == name).first()

from db import db


class Organizer(db.Model):
    __tablename__ = 'organizer'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column('userId', db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column('name', db.String(200))
    email = db.Column('email', db.String(200))
    about = db.Column('about', db.String(1000))

    event = db.relationship('Event', backref='organizer', lazy='dynamic')

    @classmethod
    def get_by_user_id(cls, user_id):
        assert user_id is not None
        return cls.query.filter(Organizer.user_id == user_id).all()\


    @classmethod
    def get_by_user_id_organizer_id(cls, user_id, organizer_id):
        assert user_id is not None
        return cls.query.filter(Organizer.user_id == user_id,
                                Organizer.id == organizer_id).first()

    @classmethod
    def get_by_user_id_and_name(cls, user_id, name):
        assert user_id is not None
        assert name is not None
        return cls.query.filter(Organizer.user_id == user_id,
                                Organizer.name == name).first()

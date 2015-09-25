from models import db
from sqlalchemy.orm import relationship
import datetime


class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    domain_id = db.Column(db.Integer, db.ForeignKey('domain.id'))
    email = db.Column(db.String(60), unique=True, nullable=False)
    first_name = db.Column(db.String(255))
    last_name = db.Column(db.String(255))
    name = db.Column(db.String(127))
    password = db.Column(db.String(512))
    device_token = db.Column(db.String(64))
    expiration = db.Column(db.DateTime)
    mobile_version = db.Column(db.String(10))
    default_culture_id = db.Column(db.Integer, db.ForeignKey('culture.id'))
    phone = db.Column(db.String(50))
    get_started_data = db.Column(db.String(127))
    registration_key = db.Column(db.String(512))
    reset_passsword_key = db.Column(db.String(512))
    registration_id = db.Column(db.String(512))
    added_time = db.Column(db.DateTime, default=datetime.datetime.now())
    updated_time = db.Column(db.DateTime)
    dice_user_id = db.Column(db.Integer)

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return unicode(self.id)

    def __repr__(self):
        return "<email (email=' %r')>" % self.email



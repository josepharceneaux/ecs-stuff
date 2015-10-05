import time
from db import db
from candidate import Candidate

class RatingTag(db.Model):
    __tablename__ = 'rating_tag'
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column('Description', db.String(100))
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=time.time())

    # Relationships
    candidates = db.relationship('Candidate', secondary="candidate_rating")

    def __repr__(self):
        return "<RatingTag (desctiption=' %r')>" % self.description


class RatingTagUser(db.Model):
    __tabelname__ = 'rating_tag_user'
    rating_tag_id = db.Column('RatingTagId', db.Integer, db.ForeignKey('rating_tag.id'), primary_key=True)
    user_id = db.Column('UserId', db.Integer, db.ForeignKey('user.id'), primary_key=True)
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=time.time())
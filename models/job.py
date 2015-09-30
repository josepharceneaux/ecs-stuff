from models import db
from user import User
from sqlalchemy.orm import relationship, backref
import time


class JobOpening(db.Model):
    __tablename__ = 'job_opening'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column('UserId', db.Integer, db.ForeignKey('user.id'))
    job_code = db.Column('JobCode', db.String(100))
    description = db.Column('Description', db.String(500))
    title = db.Column('Title', db.String(150))
    added_time = db.Column('AddedTime', db.TIMESTAMP, default=time.time())

    # Relationship
    resumes = relationship('Resume', backref='job_opening')

    def __repr__(self):
        return "<JobOpening (title=' %r')>" % self.title


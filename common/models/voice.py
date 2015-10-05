import time
from datetime import datetime
from db import db


class VoiceComment(db.Model):
    __tablename__ = 'voice_comment'
    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column('CandidatedId', db.Integer, db.ForeignKey('candidate.id'))
    list_order = db.Column('ListOrder', db.Integer)
    filename = db.Column('Filename', db.String(260))
    added_time = db.Column('AddedTime', db.DateTime, default=datetime.now())
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=time.time())
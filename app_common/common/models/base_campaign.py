__author__ = 'basit'

from datetime import datetime
from sqlalchemy.orm import relationship

from db import db
from event import Event
from email_campaign import EmailCampaign


class BaseCampaign(db.Model):
    __tablename__ = 'base_campaign'
    id = db.Column('id', db.Integer, primary_key=True)
    user_id = db.Column('UserId', db.BIGINT, db.ForeignKey('user.Id', ondelete='CASCADE'))
    name = db.Column('name', db.String(127), nullable=False)
    description = db.Column('description', db.Text(65535))
    added_datetime = db.Column('added_datetime', db.DateTime, default=datetime.utcnow)

    # Relationships
    events = relationship('Event', lazy='dynamic', cascade='all, delete-orphan',
                          passive_deletes=True, backref='base_campaign')

    email_campaigns = relationship('EmailCampaign', lazy='dynamic', cascade='all, delete-orphan',
                                   passive_deletes=True, backref='base_campaign')


class BaseCampaignEvent(db.Model):
    __tablename__ = 'base_campaign_event'
    id = db.Column(db.Integer, primary_key=True)
    base_campaign_id = db.Column('base_campaign_id', db.Integer, db.ForeignKey('base_campaign.id', ondelete='CASCADE'))
    event_id = db.Column('event_id', db.Integer, db.ForeignKey('event.id', ondelete='CASCADE'))
    added_datetime = db.Column('added_datetime', db.DateTime, default=datetime.utcnow)

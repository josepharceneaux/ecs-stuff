# TODO ; let's put a nice comment here at the top
import datetime
from db import db
from sqlalchemy.orm import relationship
from candidate import Candidate

__author__ = 'Zohaib Ijaz <mzohaib.qc@gmail.com>'


class PushCampaign(db.Model):
    # TODO comment at the start of the class
    __tablename__ = 'push_campaign'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    # TODO ; Is the body text limited because of OneSignal limitation?
    body_text = db.Column(db.String(255))
    url = db.Column(db.String(255))
    scheduler_task_id = db.Column(db.String(50))
    added_datetime = db.column(db.DateTime)
    start_datetime = db.column(db.DateTime)
    end_datetime = db.column(db.DateTime)
    frequency_id = db.Column(db.Integer, db.ForeignKey('frequency.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.Id', ondelete='CASCADE'))

    # Relationships

    blasts = relationship('PushCampaignBlast', cascade='all, delete-orphan',
                          passive_deletes=True, backref='campaign', lazy='dynamic')

    smartlists = relationship('PushCampaignSmartlist', cascade='all, delete-orphan',
                              passive_deletes=True, backref='campaign', lazy='dynamic')

    def __repr__(self):
        return "<PushCampaign ( = %r)>" % self.body_text

    @classmethod
    def get_by_user_id(cls, user_id):
        assert isinstance(user_id, (int, long)) and user_id > 0, 'User id is not valid integer'
        return cls.query.filter_by(user_id=user_id).all()

    @classmethod
    def get_by_id_and_user_id(cls, _id, user_id):
        assert isinstance(_id, (int, long)) and _id > 0, 'PushCampaign id is not valid integer'
        assert isinstance(user_id, (int, long)) and user_id > 0, 'User id is not valid integer'
        return cls.query.filter_by(id=_id, user_id=user_id).first()


class PushCampaignBlast(db.Model):
    __tablename__ = 'push_campaign_blast'
    id = db.Column(db.Integer, primary_key=True)
    sends = db.Column(db.Integer, default=0)
    clicks = db.Column(db.Integer, default=0)
    campaign_id = db.Column(db.Integer, db.ForeignKey('push_campaign.id', ondelete='CASCADE'))
    updated_time = db.Column(db.TIMESTAMP, default=datetime.datetime.now())

    # Relationships
    blast_sends = relationship('PushCampaignSend', cascade='all, delete-orphan',
                               passive_deletes=True, backref='blast', lazy='dynamic')

    def __repr__(self):
        return "<PushCampaignBlast (Sends: %s, Clicks: %s)>" % (self.sends, self.clicks)


class PushCampaignSend(db.Model):
    __tablename__ = 'push_campaign_send'
    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidate.Id', ondelete='CASCADE'))
    sent_datetime = db.Column(db.DateTime, default=datetime.datetime.now())
    campaign_blast_id = db.Column(db.Integer, db.ForeignKey("push_campaign_blast.id", ondelete='CASCADE'),
                                  nullable=False)

    # Relationships
    push_campaign_sends_url_conversions = relationship('PushCampaignSendUrlConversion',
                                                       cascade='all,delete-orphan',
                                                       passive_deletes=True,
                                                       backref='send')

    def __repr__(self):
        return "<PushCampaignSend (one_signal_notification_id: %s, candidate_id: %s)>" % (self.one_signal_notification_id, self.candidate_id)

    @classmethod
    def get_by(cls, _id=0, campaign_id=0, candidate_id=0):
        """
        This class method returns push_campaign_send objects based on given conditions:
            1. if `_id` (primary key) is given, return object with that id if found otherwise None
            2. if `campaign_id` and `candidate_id` both are given then return one object based on these ids
            3. if only `campaign_id` is given, return a list of objects that belong to a specific push campaign
            4. if only `candidate_id` is given then return objects associated with that candidate
            5. otherwise return None
        :param _id: primary_key for push_campaign_send object
        :param campaign_id: id of push campaign that is associated with this send
        :param candidate_id: candidate id associated with this send
        :return:
        """

        # TODO ; I see what are you doing here and nice try. But there is an issue, looking at the method's signature
        # it gives me impression that I can get the obj even if I give all 3 which isn't the case. I think we need
        # separate methods for claity. Or we can write a generic get_by() in the base model class that takes any parameter
        # adn then see if the parameter matches with any of the class attributes and then return the value. Or may be
        # SQLAlchemy already has a method like that built-in

        if _id:
            return cls.get_by_id(_id)
        elif isinstance(campaign_id,
                        (int, long)) and campaign_id and isinstance(candidate_id,
                                                                             (int, long)) and candidate_id:
            return cls.query.filter_by(campaign_id=campaign_id, candidate_id=candidate_id).first()
        elif isinstance(campaign_id, (int, long)) and campaign_id:
            return cls.query.filter_by(campaign_id=campaign_id).all()
        elif isinstance(candidate_id, (int, long)) and candidate_id:
            return cls.query.filter_by(candidate_id=candidate_id).all()


class PushCampaignSmartlist(db.Model):
    __tablename__ = 'push_campaign_smartlist'
    id = db.Column(db.Integer, primary_key=True)
    smartlist_id = db.Column(db.Integer, db.ForeignKey("smart_list.Id", ondelete='CASCADE'),
                             nullable=False)
    campaign_id = db.Column(db.Integer, db.ForeignKey("push_campaign.id", ondelete='CASCADE'), nullable=False)
    updated_time = db.Column(db.TIMESTAMP, default=datetime.datetime.now())

    def __repr__(self):
        return '<PushCampaignSmartlist (id = %r)>' % self.id

    @classmethod
    def get_by_campaign_id(cls, campaign_id):
        assert isinstance(campaign_id, (int, long)) and campaign_id > 0, \
            'PushCampaign Id should be a valid positive number'
        return cls.query.filter_by(campaign_id=campaign_id).all()

    @classmethod
    def get_by_campaign_id_and_smartlist_id(cls, campaign_id, smartlist_id):
        assert isinstance(campaign_id, (int, long)) and campaign_id > 0, \
            'PushCampaign Id should be a valid positive number'
        # TODO ; following message should mention smartlist_id
        assert isinstance(smartlist_id, (int, long)) and smartlist_id > 0, \
            'PushCampaign Id should be a valid positive number'
        return cls.query.filter_by(
            campaign_id=campaign_id,
            smartlist_id=smartlist_id).first()


class PushCampaignSendUrlConversion(db.Model):
    __tablename__ = 'push_campaign_send_url_conversion'
    id = db.Column(db.Integer, primary_key=True)
    push_campaign_send_id = db.Column(db.Integer,
                                      db.ForeignKey("push_campaign_send.id", ondelete='CASCADE'),
                                      nullable=False)
    url_conversion_id = db.Column(db.Integer,
                                  db.ForeignKey("url_conversion.Id", ondelete='CASCADE'),
                                  nullable=False)

    def __repr__(self):
        return '<PushCampaignSendUrlConversion (id = %r)>' % self.id

    @classmethod
    def get_by_campaign_send_id_and_url_conversion_id(cls,
                                                      campaign_send_id,
                                                      url_conversion_id):
        assert campaign_send_id, 'No campaign_send_id given'
        assert url_conversion_id, 'No url_conversion_id given'
        return cls.query.filter(
            push_campaign_send_id=campaign_send_id,
            url_conversion_id=url_conversion_id
        ).first()

    @classmethod
    def get_by_campaign_send_id(cls, campaign_send_id):
        assert campaign_send_id, 'No campaign_send_id given'
        return cls.query.filter_by(push_campaign_send_id=campaign_send_id).first()

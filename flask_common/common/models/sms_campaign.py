__author__ = 'basit'

import datetime
from db import db
from sqlalchemy.orm import relationship


class SmsCampaign(db.Model):
    __tablename__ = 'sms_campaign'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(127))
    user_phone_id = db.Column(db.Integer, db.ForeignKey('user_phone.id', ondelete='CASCADE'))
    body_text = db.Column(db.Text)
    frequency_id = db.Column(db.Integer, db.ForeignKey('frequency.id', ondelete='CASCADE'))
    start_datetime = db.Column(db.DateTime)
    end_datetime = db.Column(db.DateTime)
    added_datetime = db.Column(db.DateTime)
    updated_time = db.Column(db.TIMESTAMP, default=datetime.datetime.now())
    scheduler_task_id = db.Column(db.String(255))

    # Relationships
    sms_campaign_blasts = relationship('SmsCampaignBlast', cascade='all, delete-orphan',
                                       passive_deletes=True, backref='sms_campaign')
    sms_campaign_smartlists = relationship('SmsCampaignSmartlist', cascade='all, delete-orphan',
                                           passive_deletes=True, backref='sms_campaign')

    def __repr__(self):
        return "<SmsCampaign (name = %r)>" % self.name

    @classmethod
    def get_by_user_phone_id(cls, user_phone_id):
        assert user_phone_id, 'No user_phone_id given'
        return cls.query.filter(cls.user_phone_id == user_phone_id).all()


class SmsCampaignBlast(db.Model):
    __tablename__ = 'sms_campaign_blast'
    id = db.Column(db.Integer, primary_key=True)
    sms_campaign_id = db.Column(db.Integer, db.ForeignKey('sms_campaign.id', ondelete='CASCADE'))
    sends = db.Column(db.Integer, default=0)
    clicks = db.Column(db.Integer, default=0)
    replies = db.Column(db.Integer, default=0)
    sent_datetime = db.Column(db.DateTime)
    updated_time = db.Column(db.TIMESTAMP, default=datetime.datetime.now())

    # Relationships
    sms_campaign_sends = relationship('SmsCampaignSend', cascade='all,delete-orphan',
                                      passive_deletes=True, backref='sms_campaign_blast')
    sms_campaign_replies = relationship('SmsCampaignReply', cascade='all,delete-orphan',
                                        passive_deletes=True, backref='sms_campaign_blast')

    def __repr__(self):
        return "<SmsCampaignBlast (id = %r)>" % self.id

    @classmethod
    def get_by_campaign_id(cls, campaign_id):
        assert campaign_id, 'No campaign_id given'
        return cls.query.filter(cls.sms_campaign_id == campaign_id).first()


class SmsCampaignSend(db.Model):
    __tablename__ = 'sms_campaign_send'
    id = db.Column(db.Integer, primary_key=True)
    sms_campaign_blast_id = db.Column(db.Integer,
                                      db.ForeignKey('sms_campaign_blast.id', ondelete='CASCADE'))
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidate.id'))
    sent_datetime = db.Column(db.DateTime)
    updated_time = db.Column(db.TIMESTAMP, default=datetime.datetime.now())

    # Relationships
    sms_campaign_sends_url_conversions = relationship('SmsCampaignSendUrlConversion',
                                                      cascade='all,delete-orphan',
                                                      passive_deletes=True,
                                                      backref='sms_campaign_send')

    def __repr__(self):
        return "<SmsCampaignSend (id = %r)>" % self.id

    @classmethod
    def get_by_blast_id_and_candidate_id(cls, campaign_blast_id, candidate_id):
        assert campaign_blast_id, 'No campaign_blast_id given'
        assert candidate_id, 'No candidate_id given'
        return cls.query.filter(
            db.and_(
                cls.sms_campaign_blast_id == campaign_blast_id,
                cls.candidate_id == candidate_id,
            )
        ).first()

    @classmethod
    def get_by_candidate_id(cls, candidate_id):
        assert candidate_id, 'No candidate_id given'
        return cls.query.order_by(-cls.sent_datetime).filter(
            cls.candidate_id == candidate_id).first()

    @classmethod
    def get_by_blast_id(cls, campaign_blast_id):
        assert campaign_blast_id, 'No campaign_blast_id given'
        return cls.query.filter(cls.sms_campaign_blast_id == campaign_blast_id).all()


class SmsCampaignReply(db.Model):
    __tablename__ = 'sms_campaign_reply'
    id = db.Column(db.Integer, primary_key=True)
    sms_campaign_blast_id = db.Column(db.Integer,
                                      db.ForeignKey('sms_campaign_blast.id', ondelete='CASCADE'))
    body_text = db.Column(db.Text)
    candidate_phone_id = db.Column(db.Integer,
                                   db.ForeignKey('candidate_phone.id', ondelete='CASCADE'))
    added_datetime = db.Column(db.DateTime, default=datetime.datetime.now())

    def __repr__(self):
        return "<SmsCampaignReply (id = %r)>" % self.id

    @classmethod
    def get_by_blast_id_and_candidate_phone_id(cls, campaign_blast_id, candidate_phone_id):
        assert campaign_blast_id, 'No campaign_blast_id given'
        assert candidate_phone_id, 'No candidate_phone_id given'
        return cls.query.filter(
            db.and_(
                cls.sms_campaign_blast_id == campaign_blast_id,
                cls.candidate_phone_id == candidate_phone_id
            )
        ).first()

    @classmethod
    def get_by_candidate_phone_id(cls, candidate_phone_id):
        assert candidate_phone_id, 'No candidate_phone_id given'
        return cls.query.filter(cls.candidate_phone_id == candidate_phone_id).first()


class SmsCampaignSmartlist(db.Model):
    __tablename__ = 'sms_campaign_smartlist'
    id = db.Column(db.Integer, primary_key=True)
    smartlist_id = db.Column(db.Integer, db.ForeignKey("smart_list.id", ondelete='CASCADE'),
                             nullable=False)
    sms_campaign_id = db.Column(db.Integer, db.ForeignKey("sms_campaign.id", ondelete='CASCADE'),
                                nullable=False)
    updated_time = db.Column(db.TIMESTAMP, default=datetime.datetime.now())

    def __repr__(self):
        return '<SmsCampaignSmartlist (id = %r)>' % self.id

    @classmethod
    def get_by_campaign_id(cls, campaign_id):
        assert campaign_id, 'No campaign_id given'
        return cls.query.filter(cls.sms_campaign_id == campaign_id).all()

    @classmethod
    def get_by_campaign_id_and_smartlist_id(cls, campaign_id, smartlist_id):
        assert campaign_id, 'No campaign_id given'
        assert smartlist_id, 'No smartlist_id given'
        return cls.query.filter(
            db.and_(
                cls.sms_campaign_id == campaign_id,
                cls.smartlist_id == smartlist_id,
            )
        ).first()


class SmsCampaignSendUrlConversion(db.Model):
    __tablename__ = 'sms_campaign_send_url_conversion'
    id = db.Column(db.Integer, primary_key=True)
    sms_campaign_send_id = db.Column(db.Integer,
                                     db.ForeignKey("sms_campaign_send.id", ondelete='CASCADE'),
                                     nullable=False)
    url_conversion_id = db.Column(db.Integer,
                                  db.ForeignKey("url_conversion.id", ondelete='CASCADE'),
                                  nullable=False)

    def __repr__(self):
        return '<SmsCampaignSendUrlConversion (id = %r)>' % self.id

    @classmethod
    def get_by_campaign_send_id_and_url_conversion_id(cls,
                                                      campaign_send_id,
                                                      url_conversion_id):
        assert campaign_send_id, 'No campaign_send_id given'
        assert url_conversion_id, 'No url_conversion_id given'
        return cls.query.filter(
            db.and_(
                cls.sms_campaign_send_id == campaign_send_id,
                cls.url_conversion_id == url_conversion_id
            )
        ).first()

    @classmethod
    def get_by_campaign_send_id(cls, campaign_send_id):
        assert campaign_send_id, 'No campaign_send_id given'
        return cls.query.filter(cls.sms_campaign_send_id == campaign_send_id).all()

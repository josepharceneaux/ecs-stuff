import datetime
from db import db
from sqlalchemy.orm import relationship

__author__ = 'Zohaib Ijaz <mzohaib.qc@gmail.com>'


class PushNotification(db.Model):
    __tablename__ = 'push_notification'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(20))
    content = db.Column(db.String(80))
    url = db.Column(db.String(255))
    frequency_id = db.Column(db.Integer, db.ForeignKey('frequency.id', ondelete='CASCADE'))
    start_datetime = db.Column(db.DateTime)
    end_datetime = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'))

    # Relationships
    push_notification_blast = relationship('PushNotificationBlast', cascade='all, delete-orphan',
                                           passive_deletes=True, backref='push_notification')
    smartlists = relationship('PushNotificationSmartlist', cascade='all, delete-orphan',
                                           passive_deletes=True, backref='push_notification')

    def __repr__(self):
        return "<PushNotification ( = %r)>" % self.content

    @classmethod
    def get_by_user_id(cls, user_id):
        assert isinstance(user_id, int) and user_id > 0, 'User id is not valid integer'
        return cls.query.filter_by(user_id=user_id).all()

    @classmethod
    def get_by_id_and_user_id(cls, _id, user_id):
        assert isinstance(_id, int) and _id > 0, 'Push notification id is not valid integer'
        assert isinstance(user_id, int) and user_id > 0, 'User id is not valid integer'
        return cls.query.filter_by(id=_id, user_id=user_id).first()


class PushNotificationSend(db.Model):
    __tablename__ = 'push_notification_send'
    id = db.Column(db.Integer, primary_key=True)
    push_notification_id = db.Column(db.Integer, db.ForeignKey("push_notification.id", ondelete='CASCADE'),
                                     nullable=False)
    one_signal_notification_id = db.column(db.String)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidate.id', ondelete='CASCADE'))
    sends = db.Column(db.Integer, default=0)
    updated_time = db.Column(db.TIMESTAMP, default=datetime.datetime.now())

    @classmethod
    def get_by(cls, _id=0, push_notification_id=0, candidate_id=0):
        """
        This class method returns push_notification_send objects based on given conditions:
            1. if `_id` (primary key) is given, return object with that id if found otherwise None
            2. if `push_notification_id` and `candidate_id` both are given then return one object based on these ids
            3. if only `push_notification_id` is given, return a list of objects that belong to a specific push notification
            4. if only `candidate_id` is given then return objects associated with that candidate
            5. otherwise return None
        :param _id: primary_key for push_notification_send object
        :param push_notification_id: id of push notification that is associated with this send
        :param candidate_id: candidate id associated with this send
        :return:
        """
        if id:
            return cls.get_by_id(_id)
        elif isinstance(push_notification_id,
                        (int, long)) and push_notification_id and isinstance(candidate_id,
                                                                             (int, long)) and candidate_id:
            return cls.query.filter_by(push_notification_id=push_notification_id, candidate_id=candidate_id).first()
        elif isinstance(push_notification_id, (int, long)) and push_notification_id:
            return cls.query.filter_by(push_notification_id=push_notification_id).all()
        elif isinstance(candidate_id, (int, long)) and candidate_id:
            return cls.query.filter_by(candidate_id=candidate_id).all()



class PushNotificationBlast(db.Model):
    __tablename__ = 'push_notification_blast'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(20))
    content = db.Column(db.String(80))
    url = db.Column(db.String(255))
    sends = db.Column(db.Integer, default=0)
    clicks = db.Column(db.Integer, default=0)
    push_notification_id = db.Column(db.Integer, db.ForeignKey('push_notification.id', ondelete='CASCADE'))
    updated_time = db.Column(db.TIMESTAMP, default=datetime.datetime.now())

    def __repr__(self):
        return "<PushNotificationBlast (Sends: %s, Clicks: %s)>" % (self.sends, self.clicks)


class PushNotificationSmartlist(db.Model):
    __tablename__ = 'push_notification_smartlist'
    id = db.Column(db.Integer, primary_key=True)
    smartlist_id = db.Column(db.Integer, db.ForeignKey("smart_list.id", ondelete='CASCADE'),
                             nullable=False)
    push_notification_id = db.Column(db.Integer, db.ForeignKey("push_notification.id", ondelete='CASCADE'),
                                     nullable=False)
    updated_time = db.Column(db.TIMESTAMP, default=datetime.datetime.now())

    def __repr__(self):
        return '<PushNotificationSmartlist (id = %r)>' % self.id

    @classmethod
    def get_by_push_notification_id(cls, push_notification_id):
        assert isinstance(push_notification_id, (int, long)) and push_notification_id > 0, \
            'PushNotification Id should be a valid positive number'
        return cls.query.filter_by(push_notification_id=push_notification_id).all()

    @classmethod
    def get_by_push_notification_id_and_smartlist_id(cls, push_notification_id, smartlist_id):
        assert isinstance(push_notification_id, (int, long)) and push_notification_id > 0, \
            'PushNotification Id should be a valid positive number'
        assert isinstance(smartlist_id, (int, long)) and smartlist_id > 0, \
            'PushNotification Id should be a valid positive number'
        return cls.query.filter_by(
            push_notification_id=push_notification_id,
            smartlist_id=smartlist_id).first()

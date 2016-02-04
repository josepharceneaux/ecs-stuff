__author__ = 'erikfarmer'
from db import db


class WidgetPage(db.Model):
    __tablename__ = 'widget_page'
    id = db.Column('Id', db.BIGINT, primary_key=True)
    candidate_source_id = db.Column('CandidateSourceId', db.Integer, db.ForeignKey('candidate_source.id'))
    unique_key = db.Column('UniqueKey', db.String(255))
    email_source = db.Column('EmailSource', db.String(255))
    page_views = db.Column('PageViews', db.Integer)
    reply_address = db.Column('ReplyAddress', db.String(255))
    request_email_html = db.Column('RequestEmailHtml', db.Text())
    request_email_subject = db.Column('RequestEmailSubject', db.String(255))
    request_email_text = db.Column('RequestEmailText', db.Text())
    sign_ups = db.Column('SignUps', db.Integer)
    updated_time = db.Column('UpdatedTime', db.DateTime)
    url = db.Column('Url', db.String(500))
    user_id = db.Column('UserId', db.BIGINT, db.ForeignKey('user.id'))
    widget_name = db.Column('WidgetName', db.String(63))
    welcome_email_text = db.Column('WelcomeEmailText', db.Text())
    welcome_email_html = db.Column('WelcomeEmailHtml', db.Text())
    welcome_email_subject = db.Column('WelcomeEmailSubject', db.String(255))

    def __repr__(self):
        return "<WidgetPage (id = {})>".format(self.id)

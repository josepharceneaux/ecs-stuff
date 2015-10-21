from sqlalchemy.orm import relationship
from db import db


class Domain(db.Model):
    __tablename__ = 'domain'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column('name', db.String(50), unique=True, default=0)
    added_time = db.Column('addedTime', db.DateTime)
    organization_id = db.Column('organizationId', db.Integer, db.ForeignKey('organization.id'))
    default_tracking_code = db.Column('defaultTrackingCode', db.String(255))
    default_from_name = db.Column('defaultFromName', db.String(255))
    default_culture_id = db.Column('defaultCultureId', db.Integer, db.ForeignKey('culture.id'), nullable=False)
    settings_json = db.Column('settingsJson', db.String(1000))
    dice_company_id = db.Column('diceCompanyId', db.Integer)

    user = relationship('User', backref='domain')

    def __init__(self, name=None):
        self.name = name

    def __repr__(self):
        return '<Domain %r>' % self.name

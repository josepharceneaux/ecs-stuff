from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from base import ModelBase as Base


class Domain(Base):
    __tablename__ = 'domain'
    id = Column(Integer, primary_key=True)
    name = Column('name', String(50), unique=True, default=0)
    usage_limitation = Column('usageLimitation', Integer)
    expiration = Column('expiration', DateTime)
    addedTime = Column('addedTime', DateTime)
    organization_id = Column('organizationId', Integer, ForeignKey('organization.id'))
    is_fair_check_on = Column('isFairCheckOn', Integer, default=0)
    is_active = Column('isActive', Integer)
    default_tracking_code = Column('defaultTrackingCode', String(255))
    default_from_name = Column('defaultFromName', String(255))
    default_culture_id = Column('defaultCultureId', Integer, ForeignKey('culture.id'), nullable=False)
    settings_json = Column('settingsJson', String(1000))
    dice_company_id = Column('diceCompanyId', Integer)

    user = relationship('User', backref='domain')

    def __init__(self, name=None):
        self.name = name

    def __repr__(self):
        return '<Domain %r>' % self.name

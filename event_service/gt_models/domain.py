from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship, backref
from base import ModelBase as Base


class Domain(Base):
    __tablename__ = 'domain'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, default=0)
    usageLimitation = Column(Integer)
    expiration = Column(DateTime)
    addedTime = Column(DateTime)
    organizationId = Column(Integer, ForeignKey('organization.id'))
    isFairCheckOn = Column(Integer, default=0)
    isActive = Column(Integer)
    defaultTrackingCode = Column(String(255))
    defaultFromName = Column(String(255))
    defaultCultureId = Column(Integer, ForeignKey('culture.id'), nullable=False)
    settingsJson = Column(String(1000))
    diceCompanyId = Column(Integer)

    user = relationship('User', backref='domain')

    def __init__(self, name=None):
        self.name = name

    def __repr__(self):
        return '<Domain %r>' % (self.name)

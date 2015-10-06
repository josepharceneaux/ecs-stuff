import datetime
from db import db



class Product(db.Model):
    __tablename__ = 'product'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column('Name', db.String(100))
    notes = db.Column('Notes', db.String(500))
    updated_time = db.Column('UpdatedTime', db.DateTime, default=datetime.datetime.now())

    def __repr__(self):
        return "<Product (name=' %r')>" % self.name

    @classmethod
    def get_by_name(cls, vendor_name):
        assert vendor_name is not None
        return cls.query.filter(
            db.and_(
                Product.name == vendor_name
            )
        ).first()


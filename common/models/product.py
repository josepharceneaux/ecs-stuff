from db import db
import time


class Product(db.Model):
    __tablename__ = 'product'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column('Name', db.String(100))
    notes = db.Column('Notes', db.String(500))
    updated_time = db.Column('UpdatedTime', db.TIMESTAMP, default=time.time())

    def __repr__(self):
        return "<Product (Name)=' %r>'" % self.name

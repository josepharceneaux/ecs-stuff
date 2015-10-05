from sqlalchemy import Column, Integer, String, and_
from base import ModelBase as Base


class Product(Base):
    __tablename__ = 'product'
    id = Column(Integer, primary_key=True)
    name = Column('name', String(100))
    notes = Column('notes', String(500))

    def __repr__(self):
        return '<Name %r>' % self.name

    @classmethod
    def get_by_name(cls, vendor_name):
        assert vendor_name is not None
        return cls.query.filter(
            and_(
                Product.name == vendor_name
            )
        ).first()

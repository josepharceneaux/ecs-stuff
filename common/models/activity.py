from db import db
from sqlalchemy import Column, Integer, String, DateTime, \
    ForeignKey, and_


class Activity(db.Model):
    __tablename__ = 'activity'
    id = Column(Integer, primary_key=True)
    added_time = Column('addedTime', DateTime)
    source_table = Column('sourceTable', String(127))
    source_id = Column('sourceId', Integer)
    type = Column('type', Integer)
    user_id = Column('userId', Integer, ForeignKey('user.id'))
    params = Column('params', String(1000))

    @classmethod
    def get_by_user_id_params_type_source_id(cls, user_id, params, type, source_id):
        assert user_id is not None
        return cls.query.filter(
            and_(
                Activity.user_id == user_id,
                Activity.params == params,
                Activity.type == type,
                Activity.source_id == source_id,
            )
        ).first()

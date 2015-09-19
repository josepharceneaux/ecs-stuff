from sqlalchemy import Column, Integer, String, DateTime, \
    ForeignKey, and_
from sqlalchemy.orm import relationship
from base import ModelBase as Base


class Activity(Base):
    __tablename__ = 'activity'
    id = Column(Integer, primary_key=True)
    addedTime = Column(DateTime)
    sourceTable = Column(String(127))
    sourceId = Column(Integer)
    type = Column(Integer)
    userId = Column(Integer, ForeignKey('user.id'))
    params = Column(String(1000))

    @classmethod
    def get_by_user_id_params_type_source_id(cls, user_id, params, type, source_id):
        assert user_id is not None
        return cls.query.filter(
            and_(
                Activity.userId == user_id,
                Activity.params == params,
                Activity.type == type,
                Activity.sourceId == source_id,
            )
        ).first()

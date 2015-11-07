from db import db


class Activity(db.Model):
    __tablename__ = 'activity'
    id = db.Column(db.Integer, primary_key=True)
    added_time = db.Column('addedTime', db.DateTime)
    source_table = db.Column('sourceTable', db.String(127))
    source_id = db.Column('sourceId', db.Integer)
    type = db.Column('type', db.Integer)
    user_id = db.Column('userId', db.Integer, db.ForeignKey('user.id'))
    params = db.Column('params', db.String(1000))

    @classmethod
    def get_by_user_id_params_type_source_id(cls, user_id, params, type, source_id):
        assert user_id
        return cls.query.filter(
            db.and_(
                Activity.user_id == user_id,
                Activity.params == params,
                Activity.type == type,
                Activity.source_id == source_id,
            )
        ).first()

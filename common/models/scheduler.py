__author__ = 'basit'
from sqlalchemy import and_
from db import db


class SchedulerTask(db.Model):
    __tablename__ = 'scheduler_task'
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.String(255))
    status = db.Column(db.String(50))
    next_run_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)

    def __repr__(self):
        return "<SchedulerTask (id=' %r')>" % self.id

    @classmethod
    def get_by_job_id(cls, job_id):
        assert job_id
        return cls.query.filter(
            and_(
                cls.job_id == job_id
            )
        ).first()

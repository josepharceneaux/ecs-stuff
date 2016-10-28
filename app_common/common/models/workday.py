"""
Database classes for ATS service.
"""

__author__ = 'Joseph Arceneaux'


from db import db


class WorkdayTable(db.Model):
    """
    Class representing the Workday candidate table.
    """
    __tablename__ = 'workday_ats'
    id = db.Column(db.Integer, primary_key=True)
    ats_candidate_id = db.Column(db.Integer)
    workday_reference = db.Column(db.Text)
    pre_hire_reference = db.Column(db.Text)
    worker_reference = db.Column(db.Text)
    name_data = db.Column(db.Text)
    contact_data = db.Column(db.Text)
    social_media_data = db.Column(db.Text)
    status_data = db.Column(db.Text)
    job_application_data = db.Column(db.Text)
    prospect_data = db.Column(db.Text)
    candidate_id_data = db.Column(db.Text)

    def __repr__(self):
        return "<Workday ATS (name = %r)>" % self.name

    @classmethod
    def get_by_reference(cls, reference):
        """
        Return a Workday candidate identified by Workday reference.

        :param string reference: The Workday reference used to identify this candidate.
        """
        assert isinstance(reference, basestring), 'Reference should be a string'
        return cls.query.filter_by(workday_reference=reference).first()

    @classmethod
    def get_by_ats_id(cls, ats_id):
        """
        Return a Workday candidate identified by an ATSCandidate id.
        """
        return cls.query.filter_by(ats_candidate_id=ats_id).first()

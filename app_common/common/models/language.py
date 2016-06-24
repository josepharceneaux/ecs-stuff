from db import db
from candidate import CandidateLanguage


class Language(db.Model):
    __tablename__ = 'language'
    id = db.Column('Id', db.Integer, primary_key=True)
    name = db.Column('Name', db.String(200))
    code = db.Column('Code', db.String(3), unique=True)

    # Relationships
    candidate_languages = db.relationship('CandidateLanguage', backref='language')

    def __repr__(self):
        return "<Language (code=' %r')>" % self.code

# from db import db
# from user import Domain
#
#
# class Organization(db.Model):
#     __tablename__ = 'organization'
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(255), unique=True)
#     notes = db.Column(db.String(1000))
#
#     domain = db.relationship('Domain', backref='organization')
#
#     def __init__(self, name=None, notes=None):
#         self.name = name
#         self.notes = notes
#
#     def __repr__(self):
#         return '<Organization %r>' % self.name

from db import db

class Migration(db.Model):
    __tablename__ = 'migration'
    id = db.Column('Id', db.Integer, primary_key=True)
    name = db.Column('Name', db.String(200))
    run_at_timestamp = db.Column('RunAtTimestamp', db.DateTime, default=datetime.datetime.now())

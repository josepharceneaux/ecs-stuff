__author__ = 'ufarooqi'

from flask import Flask
from oauth.models import *
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.script import Manager
from flask.ext.migrate import Migrate, MigrateCommand

app = Flask(__name__)
app.config.from_object('config')

db = SQLAlchemy(app)
db.metadata.reflect(db.engine, only=['user'])

migrate = Migrate(app, db)
manager = Manager(app)


@manager.command
def add_roles_to_existing_users():
    # Get all existing roles and user (probably 2)
    roles = DomainRole.all().get('roles')
    existing_users = User.query.all()
    if len(roles) and len(existing_users):
        for existing_user in existing_users:
            UserScopedRoles.add_roles(existing_user.id, roles)

if __name__ == '__main__':
    manager.run()

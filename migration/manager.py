from flask import Flask
from flask.ext.script import Manager
from flask.ext.migrate import Migrate, MigrateCommand
from common.models.db import db
from common.models.user import *

app = Flask(__name__)
app.config.from_object('config')

db.init_app(app)
db.app = app

migrate = Migrate(app, db)
manager = Manager(app)
manager.add_command('db', MigrateCommand)


@manager.command
def add_roles_to_existing_users():
    # Get all existing roles and user (probably 2)
    roles = DomainRole.all().get('roles')
    existing_users = User.query.all()
    if len(roles) and len(existing_users):
        for existing_user in existing_users:
            try:
                UserScopedRoles.add_roles(existing_user.id, roles)
            except Exception:
                pass


@manager.command
def add_groups_to_user():
    db.engine.execute('\
    ALTER TABLE user\
    ADD groupId int(11),\
    ADD FOREIGN KEY (`groupId`) REFERENCES `user_groups` (`id`) ON UPDATE CASCADE ON DELETE CASCADE;')


if __name__ == '__main__':
    db.create_all()
    db.session.commit()
    manager.run()
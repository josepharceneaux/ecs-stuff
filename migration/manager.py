from flask import Flask
from flask.ext.script import Manager
from flask.ext.migrate import Migrate, MigrateCommand
from common.models.user import *

app = Flask(__name__)
app.config.from_object('config')

db.init_app(app)
db.app = app

migrate = Migrate(app, db)
manager = Manager(app)
manager.add_command('db', MigrateCommand)


@manager.command
def add_admin_roles_to_existing_users():
    # Create Admin roles if they didn't exist already in Database
    if not DomainRole.get_by_name('ADMIN'):
        DomainRole.save('ADMIN')
    if not DomainRole.get_by_name('DOMAIN_ADMIN'):
        DomainRole.save('DOMAIN_ADMIN')

    customer_managers = WebAuthMembership.query.filter_by(group_id=1).all()   # Customer Managers have group_id = 1
    user_managers = WebAuthMembership.query.filter_by(group_id=2).all()  # Customer Managers have group_id = 2

    for user_manager in user_managers:
        try:
            UserScopedRoles.add_roles(user_manager.user_id, ['DOMAIN_ADMIN'])
        except Exception:
            pass

    for customer_manager in customer_managers:
        try:
            UserScopedRoles.add_roles(customer_manager.user_id, ['ADMIN'])
        except Exception:
            pass


@manager.command
def add_groups_to_user():
    try:
        db.engine.execute('\
        ALTER TABLE user\
        ADD userGroupId IF NOT EXISTS int(11),\
        ADD FOREIGN KEY (`userGroupId`) REFERENCES `user_group` (`id`) ON UPDATE CASCADE ON DELETE CASCADE;')
    except Exception as e:
        print e.message


if __name__ == '__main__':
    db.create_all()
    db.session.commit()
    manager.run()

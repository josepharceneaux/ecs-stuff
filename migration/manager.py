from flask import Flask
from flask.ext.script import Manager
from flask.ext.migrate import Migrate, MigrateCommand
from flask_common.common.models.db import db
from flask_common.common.models import (
    associations,
    candidate,
    candidate_edit,
    email_marketing,
    event,
    event_organizer,
    language,
    misc,
    rsvp,
    smartlist,
    talent_pools_pipelines,
    university,
    user,
    venue,
    widget
)

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
    if not user.DomainRole.get_by_name('ADMIN'):
        user.DomainRole.save('ADMIN')
    if not user.DomainRole.get_by_name('DOMAIN_ADMIN'):
        user.DomainRole.save('DOMAIN_ADMIN')

    customer_managers = user.WebAuthMembership.query.filter_by(group_id=1).all()   # Customer Managers have group_id = 1
    user_managers = user.WebAuthMembership.query.filter_by(group_id=2).all()  # User Managers have group_id = 2

    customer_managers = user.User.query.filter(user.User.id.in_([customer_manager.user_id for customer_manager in customer_managers])).all()
    user_managers = user.User.query.filter(user.User.id.in_([user_manager.user_id for user_manager in user_managers])).all()

    for user_manager in user_managers:
        try:
            user.UserScopedRoles.add_roles(user_manager, ['DOMAIN_ADMIN'])
            print "Added role DOMAIN_ADMIN to user %s" % user_manager.id
        except Exception as e:
            print "Couldn't add role DOMAIN_ADMIN to user %s because: %s" % (user_manager.id, e.message)

    for customer_manager in customer_managers:
        try:
            user.UserScopedRoles.add_roles(customer_manager, ['ADMIN'])
            print "Added role ADMIN to user %s" % customer_manager.id
        except Exception as e:
            print "Couldn't add role ADMIN to user %s because: %s" % (customer_manager.id, e.message)


@manager.command
def add_groups_to_user():
    try:
        db.engine.execute('\
        ALTER TABLE user\
        ADD userGroupId int(11),\
        ADD FOREIGN KEY (`userGroupId`) REFERENCES `user_group` (`id`) ON UPDATE CASCADE ON DELETE CASCADE;')
    except Exception as e:
        print e.message


@manager.command
def add_is_disabled_field_to_user_domain_table():
    try:
        db.engine.execute("\
        ALTER TABLE user\
        ADD is_disabled tinyint(1) NOT NULL DEFAULT '0';")
        db.engine.execute("\
        ALTER TABLE domain\
        ADD is_disabled tinyint(1) NOT NULL DEFAULT '0';")
    except Exception as e:
        print e.message


if __name__ == '__main__':
    db.create_all()
    db.session.commit()
    manager.run()

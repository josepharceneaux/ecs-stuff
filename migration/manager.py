from datetime import datetime, timedelta
from random import randint
from flask.ext.script import Manager
from flask.ext.migrate import Migrate, MigrateCommand
from app_common.common.models.db import db
from app_common.common.models import (
    associations,
    candidate,
    candidate_edit,
    email_campaign,
    event,
    event_organizer,
    language,
    misc,
    push_campaign,
    rsvp,
    smartlist,
    sms_campaign,
    talent_pools_pipelines,
    university,
    user,
    venue,
    widget
)
from app_common.common.talent_config_manager import load_gettalent_config
from app_common.common.talent_flask import TalentFlask

app = TalentFlask(__name__)
load_gettalent_config(app.config)

db.init_app(app)
db.app = app

migrate = Migrate(app, db)
manager = Manager(app)
manager.add_command('db', MigrateCommand)


@manager.command
def normalize_added_time_field_in_talent_pool_candidate_table():
    """
    This method will normalize added_time field in talent_pool_candidate table
    :return:
    """
    talent_pools = talent_pools_pipelines.TalentPool.query.with_entities(talent_pools_pipelines.TalentPool.id).all()
    for talent_pool_tuple in talent_pools:
        talent_pool = talent_pools_pipelines.TalentPool.query.get(talent_pool_tuple[0])
        added_time = talent_pool.added_time
        talent_pool_candidates = talent_pools_pipelines.TalentPoolCandidate.query.filter_by(
                talent_pool_id=talent_pool.id).all()
        for talent_pool_candidate in talent_pool_candidates:
            random_date = added_time + timedelta(days=randint(0, (datetime.utcnow() - added_time).days))
            talent_pool_candidate.added_time = random_date
        db.session.commit()

# @manager.command
# def add_admin_roles_to_existing_users():
#     # Create Admin roles if they didn't exist already in Database
#     if not user.DomainRole.get_by_name('ADMIN'):
#         user.DomainRole.save('ADMIN')
#     if not user.DomainRole.get_by_name('DOMAIN_ADMIN'):
#         user.DomainRole.save('DOMAIN_ADMIN')
#
#     customer_managers = user.WebAuthMembership.query.filter_by(group_id=1).all()   # Customer Managers have group_id = 1
#     user_managers = user.WebAuthMembership.query.filter_by(group_id=2).all()  # User Managers have group_id = 2
#
#     customer_managers = user.User.query.filter(user.User.id.in_([customer_manager.user_id for customer_manager in customer_managers])).all()
#     user_managers = user.User.query.filter(user.User.id.in_([user_manager.user_id for user_manager in user_managers])).all()
#
#     for user_manager in user_managers:
#         try:
#             user.UserScopedRoles.add_roles(user_manager, ['DOMAIN_ADMIN'])
#             print "Added role DOMAIN_ADMIN to user %s" % user_manager.id
#         except Exception as e:
#             print "Couldn't add role DOMAIN_ADMIN to user %s because: %s" % (user_manager.id, e.message)
#
#     for customer_manager in customer_managers:
#         try:
#             user.UserScopedRoles.add_roles(customer_manager, ['ADMIN'])
#             print "Added role ADMIN to user %s" % customer_manager.id
#         except Exception as e:
#             print "Couldn't add role ADMIN to user %s because: %s" % (customer_manager.id, e.message)
#
#
# @manager.command
# def add_groups_to_user():
#     try:
#         db.engine.execute('\
#         ALTER TABLE user\
#         ADD userGroupId int(11),\
#         ADD FOREIGN KEY (`userGroupId`) REFERENCES `user_group` (`id`) ON UPDATE CASCADE ON DELETE CASCADE;')
#     except Exception as e:
#         print e.message
#
#
# @manager.command
# def add_is_disabled_field_to_user_domain_table():
#     try:
#         db.engine.execute("\
#         ALTER TABLE user\
#         ADD is_disabled tinyint(1) NOT NULL DEFAULT '0';")
#         db.engine.execute("\
#         ALTER TABLE domain\
#         ADD is_disabled tinyint(1) NOT NULL DEFAULT '0';")
#     except Exception as e:
#         print e.message


if __name__ == '__main__':
    db.create_all()
    db.session.commit()
    manager.run()

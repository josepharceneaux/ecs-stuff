"""
This file entails script for adding:
    1. All roles to existing domains,
    2. All roles except delete to existing users,
    2. TalentPools to existing domains,
    3. UserGroups to existing domains,
    4. TalentPoolCandidate for each existing candidate,
    5. TalentPoolGroup for each talent-pool & user-group
"""
import time
from datetime import datetime
from user_service.user_app import app
from user_service.common.models.db import db
from user_service.common.models.user import User, UserGroup, Role, Domain, Permission, PermissionsOfRole
from user_service.common.models.talent_pools_pipelines import (
    TalentPool, TalentPoolCandidate, TalentPoolGroup, TalentPipeline
)
from user_service.common.models.smartlist import Smartlist
from user_service.common.models.candidate import Candidate


def get_permissions():
    """ Function will get and return Permission constants """
    permission_names = [key for key in Permission.PermissionNames.__dict__.keys() if not key.startswith('__')]
    print "ROLE_NAMES: {}".format(permission_names)
    return list(set(permission_names))


def add_permissions():
    """ Function will add roles to existing domains """
    print "running: add_permissions()"
    permission_names = get_permissions()

    for permission_name in permission_names:
        db.session.add(Permission(name=permission_name))
    db.session.commit()


def add_roles():
    """ Function will associated each user with every Permission except delete-roles """
    print "running: add_roles()"
    permission_names = get_permissions()
    permissions_not_allowed_for_roles = dict()
    permissions_not_allowed_for_roles['TALENT_ADMIN'] = []
    permissions_not_allowed_for_roles['DOMAIN_ADMIN'] = [Permission.PermissionNames.CAN_IMPERSONATE_USERS,
                                                         Permission.PermissionNames.CAN_DELETE_DOMAINS,
                                                         Permission.PermissionNames.CAN_ADD_DOMAINS]
    permissions_not_allowed_for_roles['ADMIN'] = permissions_not_allowed_for_roles['DOMAIN_ADMIN'] + [
        Permission.PermissionNames.CAN_EDIT_DOMAINS, Permission.PermissionNames.CAN_ADD_TALENT_POOLS,
        Permission.PermissionNames.CAN_ADD_DOMAIN_GROUPS, Permission.PermissionNames.CAN_DELETE_DOMAIN_GROUPS,
        Permission.PermissionNames.CAN_EDIT_DOMAIN_GROUPS, Permission.PermissionNames.CAN_GET_DOMAIN_GROUPS,
        Permission.PermissionNames.CAN_DELETE_TALENT_POOLS, Permission.PermissionNames.CAN_EDIT_USER_ROLE]

    permissions_not_allowed_for_roles['USER'] = permissions_not_allowed_for_roles['ADMIN'] + [
        Permission.PermissionNames.CAN_EDIT_TALENT_POOLS, Permission.PermissionNames.CAN_ADD_WIDGETS,
        Permission.PermissionNames.CAN_EDIT_WIDGETS, Permission.PermissionNames.CAN_DELETE_WIDGETS,
        Permission.PermissionNames.CAN_DELETE_USERS, Permission.PermissionNames.CAN_ADD_USERS,
        Permission.PermissionNames.CAN_DELETE_CANDIDATES]

    role_names = permissions_not_allowed_for_roles.keys()
    for role_name in role_names:
        role_id = Role.save(role_name)
        for permission_name in permission_names:
            if permission_name not in permissions_not_allowed_for_roles[role_name]:
                db.session.add(PermissionsOfRole(role_id=role_id, permission_id=Permission.get_by_name(permission_name).id))

    db.session.commit()


def add_user_group_to_domains():
    """ Function will add a 'default' UserGroup to each domain """
    print "running: add_user_group_to_domains()"
    domains = Domain.query.all()
    for domain in domains:
        user_group = UserGroup.query.filter_by(domain_id=domain.id).first()
        if not user_group:
            print "domain_id: {}".format(domain.id)
            db.session.add(UserGroup(name='default', domain_id=domain.id))
            db.session.commit()


def update_users_group_id():
    """
    Users.user_group_id will be updated if user is not already associated with a UserGroup.id
    """
    print "running: update_users_group_id()"
    users = User.query.all()
    for user in users:
        print "user in progress: {}".format(user)
        if not user.user_group_id:
            user_group = UserGroup.query.filter_by(domain_id=user.domain_id).first()
            if user_group:
                print "user_id: {}, user_group_id: {}".format(user.id, user_group.id)
                user.user_group_id = user_group.id
                db.session.commit()


def add_talent_pool():
    """ Function will add talent-pool to existing domains """
    for domain in Domain.query.all():
        print "domain in progress: {}".format(domain)
        talent_pool = TalentPool.query.filter_by(domain_id=domain.id).first()
        if not talent_pool and domain.users:
            db.session.add(TalentPool(domain_id=domain.id, user_id=domain.users[0].id, name='default'))
            db.session.commit()


def add_talent_pool_candidate():
    """ Function will add talent-pool-candidate for each candidate """
    number_of_candidates = Candidate.query.count()
    print "number_of_candidates: {}".format(number_of_candidates)
    start = 0
    while start < number_of_candidates:

        for candidate in Candidate.query.slice(start, start + 100).all():
            print "candidate in progress: {}".format(candidate)
            owner_user_id = candidate.user_id
            domain_id = User.get_domain_id(_id=owner_user_id)
            talent_pool = TalentPool.query.filter_by(domain_id=domain_id, user_id=owner_user_id).first()
            if talent_pool:
                if not TalentPoolCandidate.get(candidate_id=candidate.id, talent_pool_id=talent_pool.id):
                    db.session.add(TalentPoolCandidate(candidate_id=candidate.id, talent_pool_id=talent_pool.id))
                    db.session.commit()

        start += 100


def add_talent_pool_group():
    """ Function will associate TalentPool with UserGroup by adding TalentPoolGroup records """
    print "running: add_talent_pool_group()"
    talent_pools = TalentPool.query.all()
    print "number_of_talent_pools: {}".format(len(talent_pools))
    for talent_pool in talent_pools:
        print "talent_pool in progress: {}".format(talent_pool)
        talent_pool_id = talent_pool.id
        user_group_id = User.query.get(talent_pool.user_id).user_group_id
        tpg = TalentPoolGroup.query.filter_by(talent_pool_id=talent_pool_id).first()
        if not tpg:
            print "talent_pool_id: {}, user_group_id: {}".format(talent_pool_id, user_group_id)
            db.session.add(TalentPoolGroup(talent_pool_id=talent_pool_id, user_group_id=user_group_id))
            db.session.commit()


def add_default_talent_pipelines():
    """ Function will add TalentPipeline for every "default" TalentPool
        It will also assign domain's Smartlist to the TalentPipeline
    """
    print "running: add_default_talent_pipelines()"
    default_talent_pools = TalentPool.query.filter_by(name='default').all()
    for talent_pool in default_talent_pools:
        tp_user_id = talent_pool.user_id
        talent_pipeline = TalentPipeline.query.filter_by(talent_pool_id=talent_pool.id, user_id=tp_user_id).first()
        if talent_pipeline:  # Update smartlists
            smart_list = Smartlist.query.filter_by(user_id=tp_user_id, talent_pipeline_id=talent_pipeline.id).first()
            if not smart_list:  # Add Smartlist
                db.session.add(Smartlist(user_id=tp_user_id, talent_pipeline_id=talent_pipeline.id))
                db.session.commit()
        else:  # Add TalentPipeline & Smartlist
            talent_pipeline = TalentPipeline(name='default', talent_pool_id=talent_pool.id, user_id=tp_user_id,
                                             date_needed=datetime.utcnow())
            db.session.add(talent_pipeline)
            db.session.flush()
            # Add Smartlist
            db.session.add(Smartlist(user_id=tp_user_id, talent_pipeline_id=talent_pipeline.id))
            db.session.commit()


if __name__ == '__main__':
    print "database: {}".format(db)
    try:
        start_time = time.time()
        add_permissions()
        print "completed: add_domain_roles()\ntime: {}".format(time.time() - start_time)

        time_1 = time.time()
        add_roles()
        print "completed: add_user_roles()\ntime: {}".format(time.time() - time_1)

        time_2 = time.time()
        add_user_group_to_domains()
        print "completed: add_user_group_to_domains()\ntime: {}".format(time.time() - time_2)

        time_3 = time.time()
        update_users_group_id()
        print "completed: update_users_group_id()\ntime: {}".format(time.time() - time_3)

        time_4 = time.time()
        add_talent_pool()
        print "completed: add_talent_pool()\ntime: {}".format(time.time() - time_4)

        time_5 = time.time()
        add_talent_pool_candidate()
        print "completed: add_talent_pool_candidate()\ntime: {}".format(time.time() - time_5)

        time_5 = time.time()
        add_talent_pool_group()
        print "completed: add_talent_pool_group()\ntime: {}".format(time.time() - time_5)

        time_6 = time.time()
        add_default_talent_pipelines()
        print "completed: add_default_talent_pipelines()\ntime: {}".format(time.time() - time_6)
        print "total time: {}".format(time.time() - start_time)
    except Exception as e:
        db.session.rollback()
        print "\nUpdates failed: {}".format(e.message)

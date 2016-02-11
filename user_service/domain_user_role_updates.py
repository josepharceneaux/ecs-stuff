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
from user_service.user_app import app
from user_service.common.models.db import db
from user_service.common.models.user import (
    User, UserGroup, UserScopedRoles, Domain, DomainRole
)
from user_service.common.models.talent_pools_pipelines import (
    TalentPool, TalentPoolCandidate, TalentPoolGroup
)
from user_service.common.models.candidate import Candidate


def get_role_names():
    """ Function will get and return DomainRole constants """
    constants = DomainRole.Roles.__dict__.keys()
    for constant in constants.__iter__():
        if "__" in constant:
            constants.remove(constant)

    print "ROLE_NAMES: {}".format(constants)
    return constants


def add_domain_roles():
    """ Function will add roles to existing domains """
    print "running: add_domain_roles()"
    for role_name in get_role_names():
        domain_role = DomainRole.get_by_name(role_name=role_name)
        if not domain_role:
            db.session.add(DomainRole(role_name=role_name))
            db.session.commit()


def add_user_roles():
    """ Function will associated each user with every DomainRole except delete-roles """
    print "running: add_user_roles()"
    existing_users = User.query.all()
    domain_roles = DomainRole.query.filter(DomainRole.role_name.notlike('%delete_user%') &
                                           DomainRole.role_name.notlike('%delete_domain%') &
                                           DomainRole.role_name.notilike('%delete_talent%')).all()
    for user in existing_users:
        print "user in progress: {}".format(user)
        for role in domain_roles:
            user_scoped_role = UserScopedRoles.query.filter_by(user_id=user.id,
                                                               role_id=role.id).first()
            if not user_scoped_role:
                print "role_id: {}, user_id: {}".format(role.id, user.id)
                db.session.add(UserScopedRoles(user_id=user.id, role_id=role.id))
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

        for candidate in Candidate.query.slice(start, start + 500).all():
            print "candidate in progress: {}".format(candidate)
            owner_user_id = candidate.user_id
            domain_id = User.get_domain_id(_id=owner_user_id)
            talent_pool = TalentPool.query.filter_by(domain_id=domain_id, user_id=owner_user_id).first()
            tpc = TalentPoolCandidate.get(candidate_id=candidate.id, talent_pool_id=talent_pool.id)
            if not tpc:
                db.session.add(TalentPoolCandidate(candidate_id=candidate.id, talent_pool_id=talent_pool.id))
                db.session.commit()

        start += 500


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


if __name__ == '__main__':
    print "***** starting role updates *****"
    print "database: {}".format(db)
    try:
        start_time = time.time()
        add_domain_roles()
        print "completed: add_domain_roles()\ntime: {}".format(time.time() - start_time)

        time_1 = time.time()
        add_user_roles()
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
        print "total time: {}".format(time.time() - start_time)
    except Exception as e:
        db.session.rollback()
        print "\nUpdates failed: {}".format(e.message)

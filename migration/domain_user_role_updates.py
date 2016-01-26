"""

"""
from user_service.user_app import app
from user_service.common.models.db import db
from user_service.common.models.user import (
    User, UserGroup, UserScopedRoles, Domain, DomainRole
)
from user_service.common.models.talent_pools_pipelines import (
    TalentPool, TalentPoolCandidate, TalentPoolGroup
)


def get_role_names():
    constants = DomainRole.RoleNames.__dict__.keys()
    for constant in constants.__iter__():
        if "__" in constant:
            constants.remove(constant)
    return constants


def add_domain_roles():
    for role_name in get_role_names():
        domain_role = DomainRole.get_by_name(role_name=role_name)
        if domain_role is None:
            db.session.add(DomainRole(role_name=role_name))

    db.session.commit()


def add_user_roles():
    existing_users = User.query.all()
    domain_roles = DomainRole.query.filter(DomainRole.role_name.notlike('%delete_user%') &
                                           DomainRole.role_name.notlike('%delete_domain%')).all()
    for user in existing_users:
        for role in domain_roles:
            user_scoped_role = UserScopedRoles.query.filter_by(user_id=user.id,
                                                               role_id=role.id).first()
            if user_scoped_role is None:
                db.session.add(UserScopedRoles(user_id=user.id, role_id=role.id))

    db.session.commit()


def add_user_group_to_domains():
    domains = Domain.query.all()
    for domain in domains:
        user_group = UserGroup.query.filter_by(domain_id=domain.id).first()
        if user_group is None:
            db.session.add(UserGroup(name='default', domain_id=domain.id))

    db.session.commit()


def add_talent_pool():
    users = User.query.all()
    for user in users:
        talent_pool = TalentPool.query.filter_by(domain_id=user.domain_id,
                                                 owner_user_id=user.id).first()
        if talent_pool is None:
            talent_pool = TalentPool(domain_id=user.domain_id, owner_user_id=user.id,
                                     name='default')
            db.session.add(talent_pool)
            db.session.flush()

            user_candidates = user.candidates
            for candidate in user_candidates:
                db.session.add(TalentPoolCandidate(talent_pool_id=talent_pool.id,
                                                   candidate_id=candidate.id))

    db.session.commit()


def update_users_group_id():
    """
    Users.user_group_id will be updated if user is not already assocaited with a UserGroup.id
    """
    users = User.query.all()
    for user in users:
        if user.user_group_id is None:
            user_group = UserGroup.query.filter_by(domain_id=user.domain_id).first()
            if user_group:
                user.user_group_id = user_group.id

    db.session.commit()


def add_talent_pool_group():
    talent_pools = TalentPool.query.all()
    user_groups = UserGroup.query.all()
    for group in user_groups:
        for pool in talent_pools:
            TalentPoolGroup(talent_pool_id=pool.id, user_group_id=group.id)

    db.session.commit()


if __name__ == '__main__':
    print "starting role updates"
    try:
        add_domain_roles()
        add_user_roles()
        add_user_group_to_domains()
        add_talent_pool()
        update_users_group_id()
        add_talent_pool_group()
    except Exception as e:
        db.session.rollback()
        print "\nUpdates failed: {}".format(e.message)

from user_service.user_app import app
from user_service.common.models.db import db
from user_service.common.models.user import (
    User, UserGroup, UserScopedRoles, Domain, DomainRole
)
from user_service.common.models.talent_pools_pipelines import TalentPool, TalentPoolCandidate


def get_domain_role_names():
    constants = DomainRole.RoleNames.__dict__.keys()
    for constant in constants.__iter__():
        if "__" in constant:
            constants.remove(constant)
    return constants


def update_domain_roles():
    for role_name in get_domain_role_names():
        domain_role = DomainRole.get_by_name(role_name=role_name)
        if domain_role is None:
            db.session.add(DomainRole(role_name=role_name))

    db.session.commit()


def update_user_roles():
    existing_users = User.query.all()
    domain_roles = DomainRole.query.filter(DomainRole.role_name.notlike('%delete_user%') &
                                           DomainRole.role_name.notlike('%delete_domain%')).all()
    for user in existing_users:
        for role in domain_roles:
            db.session.add(UserScopedRoles(user_id=user.id, role_id=role.id))

    db.session.commit()


def add_user_group_to_domains():
    domains = Domain.query.all()
    for domain in domains:
        db.session.add(UserGroup(name='default', domain_id=domain.id))

    db.session.commit()


def add_talent_pool():
    users = User.query.all()
    for user in users:
        talent_pool = TalentPool(domain_id=user.domain_id, owner_user_id=user.id, name='default')
        db.session.add(talent_pool)
        db.session.flush()

        user_candidates = user.candidates
        for candidate in user_candidates:
            db.session.add(TalentPoolCandidate(talent_pool_id=talent_pool.id,
                                               candidate_id=candidate.id))

    db.session.commit()


if __name__ == '__main__':
    print "starting role updates"
    try:
        update_domain_roles()
        update_user_roles()
        add_user_group_to_domains()
        add_talent_pool()
    except Exception as e:
        db.session.rollback()
        print "\nUpdates failed: {}".format(e.message)


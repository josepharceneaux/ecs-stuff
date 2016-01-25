from user_service.user_app import app
from user_service.common.models.db import db
from user_service.common.models.user import (
    User, UserGroup, UserScopedRoles, Domain, DomainRole
)


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


def update_user_roles():
    existing_users = User.query.all()
    domain_roles = DomainRole.query.filter(DomainRole.role_name.notlike('%delete_user%') &
                                           DomainRole.role_name.notlike('%delete_domain%')).all()
    for user in existing_users:
        for role in domain_roles:
            db.session.add(UserScopedRoles(user_id=user.id, role_id=role.id))


def add_user_group_to_domains():
    domains = Domain.query.all()
    for domain in domains:
        db.session.add(UserGroup(name='default', domain_id=domain.id))


if __name__ == '__main__':
    print "starting role updates"
    try:
        update_domain_roles()
        db.session.commit()
        update_user_roles()
        db.session.commit()
        add_user_group_to_domains()
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print "\nUpdates failed: {}".format(e.message)


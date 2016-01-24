from user_service.common.models.user import DomainRole
from user_service.common.models.db import db


def get_domain_role_names():
    constants = DomainRole.RoleNames.__dict__.keys()
    for i in constants.__iter__():
        if "__" in i:
            constants.remove(i)
    return constants


def update_roles():
    for role_name in get_domain_role_names():
        domain_role = DomainRole.get_by_name(role_name=role_name)
        if domain_role is None:
            db.session.add(DomainRole(role_name=role_name))

    db.session.commit()





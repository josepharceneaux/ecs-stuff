from activity_service.common.models.db import db
from activity_service.common.models.user import User


def users_are_in_same_domain(user_id_list, request_domain):
    users = db.session.query(User).filter(db.and_(User.id.in_(user_id_list), User.domain_id == request_domain)).all()
    return len(user_id_list) == len(users)

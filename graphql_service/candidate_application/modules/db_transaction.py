from sqlalchemy.exc import SQLAlchemyError

from graphql_service.common.models.db import db
from graphql_service.common.error_handling import InternalServerError


def commit_transaction():
    try:
        db.session.commit()
    except SQLAlchemyError as db_error:
        db.session.rollback()
        raise InternalServerError(db_error.message)

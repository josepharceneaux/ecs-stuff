# Models
from flask import request
from user_service.common.models.misc import CustomField
from user_service.common.models.user import User

# Error handling
from user_service.common.error_handling import NotFoundError, ForbiddenError


def get_custom_field_if_validated(custom_field_id, user):
    """
    Function will return CustomField object if it's found and it belongs to user's domain
    :type custom_field_id:  int | long
    :type user: User
    :rtype: CustomField
    """
    # Custom field ID must be recognized
    custom_field = CustomField.get(custom_field_id)
    if not custom_field:
        raise NotFoundError("Custom field ID ({}) not recognized.".format(custom_field_id))

    # Custom field must belong to user's domain
    if request.user.role.name != 'TALENT_ADMIN' and custom_field.domain_id != user.domain_id:
        raise ForbiddenError("Not authorized")

    return custom_field

import datetime

# Models
from user_service.common.models.db import db
from user_service.common.models.misc import CustomFieldCategory

# Error handling
from user_service.common.error_handling import NotFoundError, ForbiddenError, InvalidUsage


def create_custom_field_categories(custom_field_categories, domain_id):
    """
    Function adds custom field categories to db after data validations
    :param custom_field_categories: custom field category data from the client
    :param domain_id: authenticated user's domain ID
    :return: [{"id": int}, {"id": int}, ...]
    :rtype: list[dict]
    """
    created_custom_field_categories = []

    for cf_category in custom_field_categories:

        name = cf_category['name'].strip()
        if not name:  # In case it's just a whitespace
            raise InvalidUsage('Custom field category name is required.')

        # Prevent creating duplicate custom field categories for the same domain
        cf_category_object = CustomFieldCategory.query.filter_by(domain_id=domain_id, name=name).first()
        if cf_category_object:
            raise InvalidUsage(error_message='Custom field category already exists in domain.',
                               additional_error_info={'custom_field_category_id': cf_category_object.id,
                                                      'domain_id': domain_id})

        cf_category_obj = CustomFieldCategory(domain_id=domain_id, name=name)
        db.session.add(cf_category_obj)
        db.session.flush()

        created_custom_field_categories.append(dict(id=cf_category_obj.id))

    db.session.commit()
    return created_custom_field_categories


def get_custom_field_categories(domain_id, custom_field_category_id=None):
    """
    Function will return domain's custom field category if custom field category ID is provided,
    otherwise it will return all of domain's custom field categories
    :type domain_id:  int
    :type custom_field_category_id:  int | None
    :return:
    """
    if custom_field_category_id:

        ccf_category_object = CustomFieldCategory.get(custom_field_category_id)

        # Custom field category ID must be recognized
        if not ccf_category_object:
            raise NotFoundError("Custom field category ID ({}) is not recognized.".format(custom_field_category_id))

        # Custom field category must belong to user's domain
        if ccf_category_object.domain_id != domain_id:
            raise ForbiddenError("Unauthorized custom field category")

        return {
            'custom_field_category': {
                'id': ccf_category_object.id,
                'name': ccf_category_object.name,
                'domain_id': ccf_category_object.domain_id,
                'updated_datetime': str(ccf_category_object.updated_time)
            }
        }
    else:  # return all of user's domain custom field categories
        return {
            'custom_field_categories': [
                {
                    'id': ccf_category.id,
                    'name': ccf_category.name,
                    'domain_id': ccf_category.domain_id,
                    'updated_datetime': str(ccf_category.updated_time)
                } for ccf_category in CustomFieldCategory.get_all_in_domain(domain_id)
                ]
        }


def update_custom_field_categories(domain_id, update_data, custom_field_category_id=None):
    """
    Function will update domain's custom field category if custom field category ID is provided,
      otherwise it will update multiple custom field categories.
    If multiple custom field categories need to be updated, each dict should contain cf-category's ID
    :type domain_id:  int | long
    :param update_data: a list of dicts for multiple updates or a single dict for a single cf-category update
    :type custom_field_category_id: int | long
    :return:
    """

    if custom_field_category_id:

        name = update_data['custom_field_category']['name'].strip()
        if not name:  # In case name is just a whitespace
            raise InvalidUsage('Custom field category name is required.')

        custom_field_category_query = CustomFieldCategory.query.filter_by(id=custom_field_category_id)

        # Custom field category ID must be recognized
        custom_field_category_object = custom_field_category_query.first()
        if not custom_field_category_object:
            raise NotFoundError('Custom field category ID ({}) not recognized.'.format(custom_field_category_id))

        # Custom field must belong to user's domain
        if custom_field_category_object.domain_id != domain_id:
            error_message = "Custom field category (id = {custom_field_category_id}) " \
                            "does not belong to user's domain (id = {domain_id})"
            raise ForbiddenError(error_message.format(custom_field_category_id=custom_field_category_id,
                                                      domain_id=domain_id))

        custom_field_category_query.update(dict(name=name))
        db.session.commit()

        return {'custom_field_category': {'id': custom_field_category_id}}

    else:  # Update multiple custom field categories
        return_object = []
        for data in update_data['custom_field_categories']:

            name = data['name'].strip()
            if not name:  # In case name is just a whitespace
                raise InvalidUsage('Custom field category name is required.')

            custom_field_category_id = data['id']
            custom_field_category_query = CustomFieldCategory.query.filter_by(id=custom_field_category_id)

            # Custom field category ID must be recognized
            custom_field_category_object = custom_field_category_query.first()
            if not custom_field_category_object:
                raise NotFoundError('Custom field category ID ({}) not recognized.'.format(custom_field_category_id))

            # Custom field must belong to user's domain
            if custom_field_category_object.domain_id != domain_id:
                error_message = "Custom field category (id = {custom_field_category_id}) " \
                                "does not belong to user's domain (id = {domain_id})"
                raise ForbiddenError(error_message.format(custom_field_category_id=custom_field_category_id,
                                                          domain_id=domain_id))

            custom_field_category_query.update(dict(name=name))
            db.session.commit()

            return_object.append(dict(id=custom_field_category_id))

        return {'custom_field_categories': return_object}
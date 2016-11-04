"""
File contains endpoint(s) for creating & retrieving domain custom fields
"""
# Standard libraries
import requests, json, datetime

# Flask specific
from flask import request
from flask_restful import Resource

# Models
from user_service.common.models.db import db
from user_service.common.models.misc import CustomField
from user_service.common.models.user import Permission

# Decorators
from user_service.common.utils.auth_utils import require_oauth, require_all_permissions

# Validators
from user_service.common.utils.validators import get_json_data_if_validated
from user_service.modules.json_schema import custom_fields_schema, custom_field_schema

# Error handling
from user_service.common.error_handling import InvalidUsage, NotFoundError, ForbiddenError

# Helpers
from user_service.modules.domain_custom_fields import get_custom_field_if_validated, create_custom_fields


class DomainCustomFieldsResource(Resource):
    decorators = [require_oauth()]

    @require_all_permissions(Permission.PermissionNames.CAN_ADD_DOMAIN_CUSTOM_FIELDS)
    def post(self):
        """
        Function will create custom field(s) for user's domain
        resource url:  POST /v1/custom_fields
        :return: {"custom_fields": [{"id": int}, {"id": int}, ...]}
        :rtype: dict[list[dict]]
        Usage:
            >>> data = {"custom_fields": [{"category_id": 1, "name": "job status"}]}
            >>> headers = {"Authorization": "Bearer {access_token}", "content-type": "application/json"}
            >>> requests.post(url="host/v1/custom_fields", data=json.dumps(data), headers=headers)
            <Response [201]>
        """
        # Validate and obtain json data from request body
        body_dict = get_json_data_if_validated(request, custom_fields_schema, False)

        return {
                   "custom_fields": create_custom_fields(body_dict['custom_fields'], request.user.domain_id)
               }, requests.codes.CREATED

    @require_all_permissions(Permission.PermissionNames.CAN_GET_DOMAIN_CUSTOM_FIELDS)
    def get(self, **kwargs):
        """
        Function will return domain's custom field(s)
        resource url:
             i. GET /v1/custom_fields
            ii. GET /v1/custom_fields/:id
        :return: {"custom_fields": [{"id": int}, {"id": int}, ...]}
        :rtype: dict[list[dict]]
        Usage:
            >>> headers = {"Authorization": "Bearer {access_token}"}
            >>> requests.get(url="host/v1/custom_fields", headers=headers)
            <Response [200]>
        """
        custom_field_id = kwargs.get('id')

        # Return specified custom field data
        if custom_field_id:
            # Custom field ID must be recognized & belong to user's domain
            custom_field = get_custom_field_if_validated(custom_field_id, request.user)

            return {
                'custom_field': {
                    'id': custom_field.id,
                    'domain_id': custom_field.domain_id,
                    'category_id': custom_field.category_id,
                    'name': custom_field.name,
                    'added_datetime': str(custom_field.added_time)
                }
            }

        # Return all of domain's custom fields
        return {"custom_fields": [
            {
                "id": custom_field.id,
                "domain_id": custom_field.domain_id,
                'category_id': custom_field.category_id,
                "name": custom_field.name,
                "added_datetime": str(custom_field.added_time)
            } for custom_field in CustomField.get_domain_custom_fields(request.user.domain_id)]}

    @require_all_permissions(Permission.PermissionNames.CAN_EDIT_DOMAIN_CUSTOM_FIELDS)
    def put(self, **kwargs):
        """
        Function will update domain's custom field(s)
        resource url:
             i. PUT /v1/custom_fields
            ii. PUT /v1/custom_fields/:id
        :return: {"custom_fields": [{"id": int}, {"id": int}, ...]}
        :rtype: dict[list[dict]]
        Usage:
            >>> headers = {"Authorization": "Bearer {access_token}"}
            >>> data = {"custom_fields": [{"id": 4, "name": "job status"}]}
            >>> requests.put(url="host/v1/custom_fields", headers=headers, data=json.dumps(data))
            <Response [200]>
        """
        custom_field_id = kwargs.get('id')

        # Validate and obtain json data from request body
        schema = custom_field_schema if custom_field_id else custom_fields_schema
        body_dict = get_json_data_if_validated(request, schema, False)

        # Update specified custom field
        if custom_field_id:

            # Custom field ID must be recognized & belong to user's domain
            get_custom_field_if_validated(custom_field_id, request.user)

            # Remove whitespace(s) from custom field name
            custom_field_name = body_dict['custom_field']['name'].strip()
            if not custom_field_name:  # In case name is just a whitespace
                raise InvalidUsage("Name is required for creating custom field.")

            custom_field_query = CustomField.query.filter_by(id=custom_field_id)
            custom_field_query.update(dict(name=custom_field_name))
            db.session.commit()

            return {'custom_field': {'id': custom_field_id}}

        updated_custom_field_ids = []
        for custom_field in body_dict['custom_fields']:

            # Custom field ID must be provided
            custom_field_id = custom_field.get('id')
            if not custom_field_id:
                raise InvalidUsage("Custom field ID is required for updating.")

            # Remove whitespace(s) from custom field name
            custom_field_name = custom_field['name'].strip()
            if not custom_field_name:  # In case name is just a whitespace
                raise InvalidUsage("Name is required for creating custom field.")

            custom_field_query = CustomField.query.filter_by(id=custom_field_id)

            # Custom field ID must be recognized
            cf_object = custom_field_query.first()
            if not cf_object:
                raise NotFoundError('Custom field ID ({}) not recognized.'.format(custom_field_id))

            # Custom field must belong to user's domain
            if cf_object.domain_id != request.user.domain_id:
                raise ForbiddenError('Not authorized')

            custom_field_query.update(dict(name=custom_field_name))
            updated_custom_field_ids.append(custom_field_id)

        db.session.commit()
        return {'custom_fields': [{'id': custom_field_id} for custom_field_id in updated_custom_field_ids]}

    # TODO: this endpoint should not be used since it will cause further complexity - Amir
    # @require_all_permissions(Permission.PermissionNames.CAN_DELETE_DOMAIN_CUSTOM_FIELDS)
    # def delete(self, **kwargs):
    #     """
    #     Function will delete domain's custom field(s)
    #     resource url:
    #         i. DELETE /v1/custom_fields/:id
    #     :return: {"custom_field": {"id": int}}
    #     :rtype: dict[dict]
    #     Usage:
    #         >>> headers = {"Authorization": "Bearer {access_token}"}
    #         >>> requests.delete(url="host/v1/custom_fields/4", headers=headers)
    #         <Response [200]>
    #     """
    #     custom_field_id = kwargs.get('id')
    #
    #     # Delete specified custom field
    #     if custom_field_id:
    #
    #         # Custom field ID must be recognized
    #         custom_field = CustomField.get(custom_field_id)
    #         if not custom_field:
    #             raise NotFoundError("Custom field ID ({}) not recognized.".format(custom_field_id))
    #
    #         # Custom field must belong to user's domain
    #         if request.user.role.name != 'TALENT_ADMIN' and custom_field.domain_id != request.user.domain_id:
    #             raise ForbiddenError("Not authorized")
    #
    #         db.session.delete(custom_field)
    #         db.session.commit()
    #
    #         return {'custom_field': {'id': custom_field_id}}

"""
File contains endpoint(s) for creating & retrieving domain custom field categories
"""
# Standard libraries
import json
import requests

# Flask specific
from flask import request
from flask_restful import Resource

# Models
from user_service.common.models.user import Permission

# Decorators
from user_service.common.utils.auth_utils import require_oauth, require_all_permissions

# Validators
from user_service.common.utils.validators import get_json_data_if_validated
from user_service.modules.json_schema import (
    cf_categories_schema_post, cf_category_schema_put, cf_categories_schema_put
)

# Helpers
from user_service.modules.domain_custom_field_categories import \
    create_custom_field_categories, get_custom_field_categories, update_custom_field_categories


class DomainCustomFieldCategoriesResource(Resource):
    decorators = [require_oauth()]

    @require_all_permissions(Permission.PermissionNames.CAN_EDIT_DOMAINS)
    def post(self):
        """
        Function will create custom field categories for user's domain
        resource url:  POST /v1/custom_field_categories
        :return: {"custom_field_categories": [{"id": int}, {"id": int}, ...]}
        :rtype: dict[list[dict]]
        Usage:
            >>> data = {"custom_field_categories": [{"name": "Marketing"}]}
            >>> headers = {"Authorization": "Bearer {access_token}", "content-type": "application/json"}
            >>> requests.post(url="host/v1/custom_field_categories", data=json.dumps(data), headers=headers)
            <Response [201]>
        """
        # Validate and obtain json data from request body
        body_dict = get_json_data_if_validated(request, cf_categories_schema_post, False)

        return {
                   "custom_field_categories": create_custom_field_categories(body_dict['custom_field_categories'],
                                                                             request.user.domain_id)
               }, requests.codes.CREATED

    @require_all_permissions(Permission.PermissionNames.CAN_GET_DOMAINS)
    def get(self, **kwargs):
        """
        Function will return domain's custom field category(ies)
        resource url:
             i. GET /v1/custom_field_categories
            ii. GET /v1/custom_field_categories/:id
        :return: {"custom_field_categories": [{"id": int}, {"id": int}, ...]}
        :rtype: dict[list[dict]]
        Usage:
            >>> headers = {"Authorization": "Bearer {access_token}"}
            >>> requests.get(url="host/v1/custom_field_categories", headers=headers)
            <Response [200]>
        """
        return get_custom_field_categories(domain_id=request.user.domain_id,
                                           custom_field_category_id=kwargs.get('id'))

    @require_all_permissions(Permission.PermissionNames.CAN_EDIT_DOMAINS)
    def put(self, **kwargs):
        """
        Function will update domain's custom field category(ies)
        resource url:
             i. PUT /v1/custom_field_categories
            ii. PUT /v1/custom_field_categories/:id
        :return: {"custom_field_categories": [{"id": int}, {"id": int}, ...]}
        :rtype: dict[list[dict]]
        Usage:
            >>> data = {"custom_field_categories": [{"id": 5, "name": "Marketing"}, {"id": 6, "name": "Sales"}]}
            >>> headers = {"Authorization": "Bearer {access_token}"}
            >>> requests.get(url="host/v1/custom_field_categories", headers=headers)
            <Response [200]>
        """
        # Validate and obtain json data from request body
        custom_field_category_id = kwargs.get('id')
        if custom_field_category_id:
            body_dict = get_json_data_if_validated(request, cf_category_schema_put, False)
        else:
            body_dict = get_json_data_if_validated(request, cf_categories_schema_put, False)

        return update_custom_field_categories(domain_id=request.user.domain_id,
                                              update_data=body_dict,
                                              custom_field_category_id=custom_field_category_id)

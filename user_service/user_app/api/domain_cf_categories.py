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
from user_service.modules.json_schema import (cf_schema_post, cf_schema_patch)

# Helpers
from user_service.modules.domain_custom_field_categories import (
    retrieve_domain_custom_fields, add_or_update_custom_fields
)

# Error handling
from user_service.common.error_handling import ForbiddenError


class DomainCustomFieldCategoriesResource(Resource):
    decorators = [require_oauth()]

    # TODO: update docstring
    @require_all_permissions(Permission.PermissionNames.CAN_ADD_DOMAIN_CUSTOM_FIELDS)
    def post(self):
        """
        Function will create custom field categories for user's domain
        resource url:  POST /v1/custom_field_categories
        :return: {"custom_field_categories": [{"id": int}, {"id": int}, ...]}
        :rtype: dict[list[dict]]
        Usage:
            >>> data = {
            >>> 	"custom_fields": [
            >>> 		{
            >>> 			"name": "color",
            >>> 			"categories": [
            >>> 				{
            >>> 					"name": "red",
            >>> 					"subcategories": [
            >>> 						{"name": "bright"}, {"name": "dark"}
            >>> 					]
            >>> 				},
            >>> 				{
            >>> 					"name": "green",
            >>> 					"subcategories": [
            >>> 						{"name": "bright"}, {"name": "dark"}
            >>> 					]
            >>> 				}
            >>> 			]
            >>> 		}
            >>> 	]
            >>> }
            >>> headers = {"Authorization": "Bearer {access_token}", "content-type": "application/json"}
            >>> requests.post(url="host/v1/custom_field_categories", data=json.dumps(data), headers=headers)
            <Response [201]>
        """
        # Validate and obtain json data from request body
        body_dict = get_json_data_if_validated(request, cf_schema_post, False)
        return {
                   "custom_fields": add_or_update_custom_fields(custom_fields_data=body_dict['custom_fields'],
                                                                domain_id=request.user.domain_id,
                                                                is_creating=True)
               }, requests.codes.CREATED

    # TODO: update docstring
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
        return retrieve_domain_custom_fields(domain_id=request.user.domain_id, custom_field_id=kwargs.get('id'))

    # TODO: update docstring
    @require_all_permissions(Permission.PermissionNames.CAN_EDIT_DOMAIN_CUSTOM_FIELDS)
    def patch(self, **kwargs):
        """
        Function will update domain's custom field category(ies)
        resource url:
             i. PATCH /v1/custom_field_categories
        :return: {"custom_fields": [{"id": int}, {"id": int}, ...]}
        :rtype: dict[list[dict]]
        Usage:
            >>> data = {"custom_fields": [{"id": 5, "name": "Marketing"}, {"id": 6, "name": "Sales"}]}
            >>> headers = {"Authorization": "Bearer {access_token}"}
            >>> requests.get(url="host/v1/custom_field_categories", headers=headers)
            <Response [200]>
        """
        # Validate and obtain json data from request body
        body_dict = get_json_data_if_validated(request, cf_schema_patch, False)

        return {"custom_fields": [{"id": cf_id} for cf_id in add_or_update_custom_fields(body_dict['custom_fields'],
                                                                                         request.user.domain_id)]}

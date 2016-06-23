"""
File contains resources for creating, retrieving, updating, and deleting domain area(s) of interest
"""
# Standard libraries
import requests, json

# Flask specific
from flask import request
from flask_restful import Resource

# Models
from user_service.common.models.misc import AreaOfInterest
from user_service.common.models.user import Permission

# Decorators
from user_service.common.utils.auth_utils import require_oauth, require_all_permissions

# Validators
from user_service.common.utils.validators import get_json_data_if_validated
from user_service.modules.json_schema import aoi_schema

# Helpers
from user_service.modules.domain_area_of_interest import (
    create_or_update_domain_aois, delete_domain_aoi, delete_domain_aois, retrieve_domain_aoi
)

# Error handling
from user_service.common.error_handling import InvalidUsage


class DomainAreaOfInterestResource(Resource):
    decorators = [require_oauth()]

    @require_all_permissions(Permission.PermissionNames.CAN_EDIT_DOMAINS)
    def post(self):
        """
        Function will create area(s) of interest for user's domain
        :return: {"areas_of_interest": [{"id": int}, {"id": int}, ...]}
        :rtype: dict[list[dict]]
        Usage:
            >>> data = {"areas_of_interest": [{"description": "finance"}]}
            >>> headers = {"Authorization": "Bearer {access_token}", "content-type": "application/json"}
            >>> requests.post(url="host/v1/areas_of_interest", data=json.dumps(data), headers=headers)
            <Response [201]>
        """
        # Authenticated user
        authed_user = request.user
        domain_id = authed_user.domain_id

        # Validate and get json data from request body
        body_dict = get_json_data_if_validated(request_body=request, json_schema=aoi_schema, format_checker=False)

        created_aoi_ids = create_or_update_domain_aois(domain_id, body_dict['areas_of_interest'], is_creating=True)
        return {"areas_of_interest": [{"id": cf_id} for cf_id in created_aoi_ids]}, 201

    def get(self, **kwargs):
        """
        Function will return domain's area(s) of interest
        resource url:  /v1/custom_fields
        :return: {"areas_of_interest": [{"id": int}, {"id": int}, ...]}
        :rtype: dict[list[dict]]
        Usage:
            >>> headers = {"Authorization": "Bearer {access_token}"}
            >>> requests.get(url="host/v1/custom_fields", headers=headers)
            <Response [200]>
        """
        aoi_id = kwargs.get('id')
        if aoi_id:
            return {"area_of_interest": retrieve_domain_aoi(request.user.domain_id, aoi_id)}

        return {"areas_of_interest": [
            {
                "id": aoi.id,
                "domain_id": aoi.domain_id,
                "description": aoi.name
            } for aoi in AreaOfInterest.get_domain_areas_of_interest(request.user.domain_id)]}

    @require_all_permissions(Permission.PermissionNames.CAN_EDIT_DOMAINS)
    def put(self, **kwargs):
        """
        Function will update area(s) of interest for user's domain
        :return: {"areas_of_interest": [{"id": int}, {"id": int}, ...]}
        :rtype: dict[list[dict]]
        Usage:
            >>> data = {"areas_of_interest": [{"id": 23, "description": "finance"}]}
            >>> headers = {"Authorization": "Bearer {access_token}", "content-type": "application/json"}
            >>> requests.put(url="host/v1/areas_of_interest", data=json.dumps(data), headers=headers)
            <Response [200]>
        """
        # Validate and get json data from request body
        body_dict = get_json_data_if_validated(request_body=request, json_schema=aoi_schema, format_checker=False)

        areas_of_interest = body_dict['areas_of_interest']  # required field, validated via json-schema
        domain_id = request.user.domain_id
        aoi_id_from_url = kwargs.get('id')

        # Only one record may be updated if aoi_id_from_url is provided
        if aoi_id_from_url and (len(areas_of_interest) > 1):
            raise InvalidUsage("Invalid usage")

        updated_aoi_ids = create_or_update_domain_aois(domain_id=domain_id, aois=body_dict['areas_of_interest'],
                                                       aoi_id_from_url=aoi_id_from_url, is_updating=True)
        return {"areas_of_interest": [{"id": aoi_id} for aoi_id in updated_aoi_ids]}

    @require_all_permissions(Permission.PermissionNames.CAN_EDIT_DOMAINS)
    def delete(self, **kwargs):
        """
        Function will delete domain area(s) of interest
        Endpoints:
             i. DELETE /v1/areas_of_interest        => will delete all of domain's aois
            ii. DELETE /v1/areas_of_interest/:id    => will delete a single aoi
        Usage:
            >>> headers = {"Authorization": "Bearer {access_token}", "content-type": "application/json"}
            >>> requests.delete(url="host/v1/areas_of_interest", headers=headers)
            <Response [200]>
        :return: {"areas_of_interest": [{"id": int}, {"id": int}, ...]}
        """
        aoi_id = kwargs.get('id')
        if aoi_id:  # delete specified area of interest
            delete_domain_aoi(request.user.domain_id, aoi_id)
            return {"area_of_interest": {"id": aoi_id}}
        else:  # delete all of domain's areas of interest
            deleted_aoi_ids = delete_domain_aois(request.user.domain_id)
            return {"areas_of_interest": [{"id": aoi_id} for aoi_id in deleted_aoi_ids]}

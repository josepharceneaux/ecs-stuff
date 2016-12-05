"""
File contains APIs for candidate subfields such as: Tags, Areas of Interest, etc.
"""
# Standard libraries
import json
import requests
from flask import request
from flask_restful import Resource

from candidate_service.common.error_handling import (InvalidUsage)
from candidate_service.common.models.user import Permission
from candidate_service.common.utils.auth_utils import require_oauth, require_all_permissions
from candidate_service.common.utils.custom_error_codes import CandidateCustomErrors as custom_error
from candidate_service.modules.json_schema import tag_schema
from candidate_service.modules.tags import (
    create_tags, get_tags, update_candidate_tag, update_candidate_tags, delete_tag, delete_tags
)
from candidate_service.modules.talent_cloud_search import upload_candidate_documents
from candidate_service.modules.validators import get_json_data_if_validated, get_candidate_if_validated


class CandidateTagResource(Resource):
    decorators = [require_oauth()]

    @require_all_permissions(Permission.PermissionNames.CAN_EDIT_CANDIDATES)
    def post(self, **kwargs):
        """
        Function will create tags
        Note: "description" is a required field
        Endpoint:  POST /v1/candidates/:candidate_id/tags
        Docs: http://docs.candidatetags.apiary.io/#reference/tags/tags-collections-resource/create-tags
        Example:
            >>> url = 'host/v1/candidates/4/tags'
            >>> headers = {'Authorization': 'Bearer edo9rdSKN8hYuc1zBWMfLXpXFd4ZbE'}
            >>> data = {"tags": [{"description": "python"}]}
            >>> requests.post(url=url, headers=headers, data=json.dumps(data))
        :return:  {'tags': [{'id': int}, {'id': int}, ...]}
        """
        # Get json data if exists and validate its schema
        body_dict = get_json_data_if_validated(request, tag_schema, False)

        # Description is a required field (must not be empty)
        for tag in body_dict['tags']:
            tag['name'] = tag['name'].strip().lower()  # remove whitespaces while validating
            if not tag['name']:
                raise InvalidUsage('Tag name is a required field', custom_error.MISSING_INPUT)

        # Authenticated user & candidate ID
        authed_user, candidate_id = request.user, kwargs['candidate_id']

        # Check for candidate's existence and web-hidden status
        get_candidate_if_validated(authed_user, candidate_id)

        # Create tags
        created_tag_ids = create_tags(candidate_id=candidate_id, tags=body_dict['tags'])

        # Update cloud search
        upload_candidate_documents.delay([candidate_id])

        return {'tags': [{'id': tag_id} for tag_id in created_tag_ids]}, 201

    @require_all_permissions(Permission.PermissionNames.CAN_GET_CANDIDATES)
    def get(self, **kwargs):
        """
        Function will retrieve tag(s)
        Endpoints:
             i. GET /v1/candidates/:candidate_id/tags
            ii. GET /v1/candidates/:candidate_id/tags/:id
        Example:
            >>> url = 'host/v1/candidates/4/tags' or 'host/v1/candidates/4/tags/57'
            >>> headers = {'Authorization': 'Bearer edo9rdSKN8hYuc1zBWMfLXpXFd4ZbE'}
            >>> requests.get(url=url, headers=headers)
        If tag ID is not provided in the url, all of candidate's tags will be returned
            :return:  {'tags': [{'id': int, 'description': string}, {'id': int, 'description': string}, ...]}
        If tag ID is provided in the url, a single candidate tag will be returned
            :return: {'tag': [{'description': string}]}
        """
        # Authenticated user, candidate ID, and tag ID
        authed_user, candidate_id, tag_id = request.user, kwargs['candidate_id'], kwargs.get('id')

        # Check for candidate's existence and web-hidden status
        get_candidate_if_validated(authed_user, candidate_id)

        # Retrieve tag(s)
        return get_tags(candidate_id=candidate_id, tag_id=tag_id)

    @require_all_permissions(Permission.PermissionNames.CAN_EDIT_CANDIDATES)
    def patch(self, **kwargs):
        """
        Function will update candidate's tag(s)
        Endpoints:
             i. PATCH /v1/candidates/:candidate_id/tags
            ii. PATCH /v1/candidates/:candidate_id/tags/:id
        Example:
            >>> url = 'host/v1/candidates/4/tags' or 'host/v1/candidates/4/tags/57'
            >>> headers = {'Authorization': 'Bearer edo9rdSKN8hYuc1zBWMfLXpXFd4ZbE'}
            >>> data = {"tags": [{"description": "minority"}, {"description": "remote"}]}
            >>> requests.patch(url=url, headers=headers, data=json.dumps(data))
        """
        # Get json data if exists and validate its schema
        body_dict = get_json_data_if_validated(request, tag_schema, False)

        # Description is a required field (must not be empty)
        tags, tag = body_dict.get('tags'), body_dict.get('tag')
        for tag in tags:
            tag['name'] = tag['name'].strip().lower()  # remove whitespaces while validating
            if not tag['name']:
                raise InvalidUsage('Tag name is a required field', custom_error.MISSING_INPUT)

        # Authenticated user, candidate ID, and tag ID
        authed_user, candidate_id, tag_id = request.user, kwargs['candidate_id'], kwargs.get('id')

        # If tag_id is provided in the url, it is assumed that only one candidate-tag needs to be updated
        if tag_id and len(tags) > 1:
            raise InvalidUsage("Updating multiple Tags via this resource is not permitted.", custom_error.INVALID_USAGE)

        # Check for candidate's existence and web-hidden status
        get_candidate_if_validated(authed_user, candidate_id)

        # If tag_id is provided in the url, update only one record
        if tag_id:
            return {'updated_tag': update_candidate_tag(candidate_id, tag_id, tag['name'].strip())}

        # Update tag(s)
        updated_tag_ids = update_candidate_tags(candidate_id=candidate_id, tags=tags)

        # Update cloud search
        upload_candidate_documents.delay([candidate_id])

        return {'updated_tags': [{'id': tag_id} for tag_id in updated_tag_ids]}

    @require_all_permissions(Permission.PermissionNames.CAN_EDIT_CANDIDATES)
    def delete(self, **kwargs):
        """
        Function will delete candidate's tag(s)
        Endpoints:
             i. DELETE /v1/candidates/:candidate_id/tags
            ii. DELETE /v1/candidates/:candidate_id/tags/:id
        Example:
            >>> url = 'host/v1/candidates/4/tags' or 'host/v1/candidates/4/tags/57'
            >>> headers = {'Authorization': 'Bearer edo9rdSKN8hYuc1zBWMfLXpXFd4ZbE'}
            >>> requests.delete(url=url, headers=headers)
        """
        # Authenticated user, candidate ID, and tag ID
        authed_user, candidate_id, tag_id = request.user, kwargs['candidate_id'], kwargs.get('id')

        # Check for candidate's existence and web-hidden status
        get_candidate_if_validated(authed_user, candidate_id)

        # Delete specified tag
        if tag_id:

            # Delete
            deleted_tag_id = delete_tag(candidate_id=candidate_id, tag_id=tag_id)

            # Update cloud search
            upload_candidate_documents([candidate_id])

            return {'deleted_tag': deleted_tag_id}

        # Delete all of candidate's tags
        deleted_tag_ids = delete_tags(candidate_id)

        # Update cloud search
        upload_candidate_documents.delay([candidate_id])

        # Delete all of candidate's tags
        return {'deleted_tags': deleted_tag_ids}

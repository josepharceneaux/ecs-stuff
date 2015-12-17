from flask import request
from flask_restful import Resource

from candidate_pool_service.common.utils.auth_utils import require_oauth
from candidate_pool_service.common.error_handling import ForbiddenError, NotFoundError
from candidate_pool_service.common.models.smartlist import Smartlist
from candidate_pool_service.modules.smartlists import get_candidates, create_smartlist_dict, save_smartlist, get_all_smartlists
from candidate_pool_service.modules.validators import (validate_and_parse_request_data, validate_list_belongs_to_domain,
                                                       validate_and_format_smartlist_post_data)

__author__ = 'jitesh'


class SmartlistCandidates(Resource):

    decorators = [require_oauth]

    def get(self, **kwargs):
        """
        Use this endpoint to retrieve all candidates present in list (smart or dumb list)
        Input:
            URL Arguments `smartlist_id` (Required): id of smartlist
            Accepts (query string parameters):
                fields :: comma separated values
                        `candidate_ids_only` --> returns candidate ids only
                        `count_only` --> returns only the count of candidates present in list
                        `all_fields`  --> returns all candidates' fields (all attributes)
                        'fields' parameter not present --> same as 'all' parameter --> returns all candidate fields
        :return : List of candidates present in list (smart list or dumb list)
        :rtype: json
        """
        auth_user = request.user
        smartlist_id = kwargs['smartlist_id']
        data = validate_and_parse_request_data(request.args)
        smartlist = Smartlist.query.get(smartlist_id)
        if not smartlist:
            raise NotFoundError("List id does not exists.", 404)
        if not validate_list_belongs_to_domain(smartlist, auth_user.id):
            raise ForbiddenError("Provided list does not belong to user's domain", 403)
        return get_candidates(smartlist, request.oauth_token, data['candidate_ids_only'], data['count_only'])


class SmartlistResource(Resource):
    decorators = [require_oauth]

    def get(self, **kwargs):
        """Retrieve list information
        List must belong to auth user's domain
        Call this resource from url: /v1/smartlists :: to retrieve all the smartlists in user's domain
                                     /v1/smartlists/<int:id> :: to get single smartlist

        example: http://localhost:8005/v1/smartlists/2
        Returns: List in following json format
            {
              "smartlist": {
                "total_found": 3,
                "user_id": 1,
                "id": 1,
                "name": "my list"
                "search_params": {"location": "San Jose, CA"}
              }
            }
        """
        list_id = kwargs.get('id')
        auth_user = request.user
        if list_id:
            smartlist = Smartlist.query.get(list_id)
            if not smartlist:
                raise NotFoundError("List id does not exists", 404)
            if not validate_list_belongs_to_domain(smartlist, auth_user.id):
                raise ForbiddenError("List does not belong to user's domain", 403)
            return create_smartlist_dict(smartlist, request.oauth_token)
        else:
            # Return all smartlists from user's domain
            return get_all_smartlists(auth_user, request.oauth_token)

    def post(self):
        """
        Creates list with search params or with list of candidate ids
        Input data:
            "name": Name with which smart list will be created
            "search_params": search parameters for smart list
                or  "candidate_ids": if not search_params then candidate_ids should be present
        :return: smartlist id
        """
        user_id = request.user.id
        # request.form data must pass through this function, as this will create data in desired format
        data = validate_and_format_smartlist_post_data(request.form, user_id)
        smartlist = save_smartlist(user_id=user_id, name=data.get('name'), search_params=data.get('search_params'),
                                   candidate_ids=data.get('candidate_ids'))
        return {'smartlist': {'id': smartlist.id}}, 201

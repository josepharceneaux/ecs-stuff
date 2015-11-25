from flask import request
from flask_restful import Resource

from candidate_service.common.utils.auth_utils import require_oauth
from ...modules.smartlists import get_candidates, create_smartlist_dict, save_smartlist
from ...modules.validators import (validate_and_parse_request_data, validate_list_belongs_to_domain,
                                   _validate_and_format_smartlist_post_data)
from candidate_service.common.error_handling import ForbiddenError
from candidate_service.common.models.smart_list import SmartList

__author__ = 'jitesh'


class SmartlistCandidates(Resource):

    decorators = [require_oauth]

    def get(self, **kwargs):
        """
        Use this endpoint to retrieve all candidates present in list (smart or dumb list)
        Input (query parameters):
            Accepts:
                id :: list id
                return :: comma separated values
                        candidate_ids_only --> returns only list of candidate ids not all candidate fields
                        count_only --> returns only the count of candidates present in list
                        all  --> returns candidates (all attributes) belonging to list
                        'return' parameter not present --> same as 'all' parameter --> returns candidates of list
        :return : candidates present in list (smart list or dumb list)
        :rtype: json
        """
        auth_user = request.user
        data = validate_and_parse_request_data(request.args)
        smart_list = SmartList.query.get(data['list_id'])
        if not validate_list_belongs_to_domain(smart_list, auth_user.id):
            raise ForbiddenError("Provided list does not belong to user's domain")
        return get_candidates(smart_list, data['candidate_ids_only'], data['count_only'])


class SmartlistResource(Resource):
    decorators = [require_oauth]

    def get(self, **kwargs):
        """Retrieve list information
        List must belong to auth user's domain
        Call this resource from url: /v1/smartlist/<int:id>
        example: http://localhost:8005/v1/smartlist/2
        Returns: List in following json format
            {
              "list": {
                "candidate_count": 3,
                "user_id": 1,
                "id": 1,
                "name": "my list"
              }
            }
        """
        list_id = kwargs.get('id')
        auth_user = request.user
        smart_list = SmartList.query.get(list_id)
        if not validate_list_belongs_to_domain(smart_list, auth_user.id):
            raise ForbiddenError("List does not belong to user's domain")
        return create_smartlist_dict(smart_list)

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
        data = _validate_and_format_smartlist_post_data(request.form, user_id)
        smart_list = save_smartlist(user_id=user_id, name=data.get('name'), search_params=data.get('search_params'),
                                    candidate_ids=data.get('candidate_ids'))
        return {'smartlist': {'id': smart_list.id}}

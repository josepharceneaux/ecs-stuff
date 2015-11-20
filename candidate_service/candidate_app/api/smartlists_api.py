from flask import request
from flask_restful import Resource

from candidate_service.common.utils.auth_utils import require_oauth
from ...modules.smartlists import get_candidates
from ...modules.validators import validate_and_parse_request_data, validate_list_belongs_to_domain
from candidate_service.common.error_handling import ForbiddenError
from candidate_service.common.models.smart_list import SmartList

__author__ = 'jitesh'


class SmartlistCandidates(Resource):

    decorators = [require_oauth]

    def get(self, **kwargs):
        """
        Use this endpoint to retrieve all candidates present in list (smart or dumb list)
        Input:
            Accepts:
                id :: list id (int)
                return :: comma separated values
                        candidate_ids_only --> returns only list of candidate ids not all candidate fields
                        count_only --> returns only the count of candidates present in list
                        all  --> returns candidates (all attributes) belonging to list
                        'return' parameter not present --> same as 'all' parameter --> returns candidates of list
        :return : candidates present in list (smart list or dumb list)
        :rtype: json
        """
        auth_user = request.user
        data = validate_and_parse_request_data(kwargs)
        smart_list = SmartList.query.get(data['list_id'])
        if not validate_list_belongs_to_domain(smart_list, auth_user.id):
            raise ForbiddenError("Provided list does not belong to user's domain")
        return get_candidates(smart_list, data['candidate_ids_only'], data['count_only'])


class SmartlistResource(Resource):

    def post(self, **kwargs):
        """
        Creates list with search params or with list of candidate ids
        :param kwargs:
        :return:
        """
        pass
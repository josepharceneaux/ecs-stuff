from flask import request, Blueprint, jsonify
from flask_restful import Resource

from candidate_pool_service.common.models.user import User
from candidate_pool_service.common.talent_api import TalentApi
from candidate_pool_service.common.routes import CandidatePoolApi
from candidate_pool_service.common.models.smartlist import Smartlist
from candidate_pool_service.common.utils.validators import is_number
from candidate_pool_service.common.utils.auth_utils import require_oauth
from candidate_pool_service.common.utils.api_utils import DEFAULT_PAGE, DEFAULT_PAGE_SIZE
from candidate_pool_service.modules.validators import validate_and_format_smartlist_post_data
from candidate_pool_service.common.error_handling import ForbiddenError, NotFoundError, InvalidUsage
from candidate_pool_service.candidate_pool_app.talent_pools_pipelines_utilities import get_smartlist_candidates
from candidate_pool_service.modules.smartlists import create_smartlist_dict, save_smartlist, get_all_smartlists
from candidate_pool_service.candidate_pool_app.talent_pools_pipelines_utilities import get_stats_generic_function

__author__ = 'jitesh'

smartlist_blueprint = Blueprint('smartlist_api', __name__)


class SmartlistCandidates(Resource):

    decorators = [require_oauth()]

    def get(self, **kwargs):
        """
        Use this endpoint to retrieve all candidates present in list (smart or dumb list)
        Input:
            URL Arguments `smartlist_id` (Required): id of smartlist
            Accepts (query string parameters):
                fields :: comma separated values
                sort_by ::  Sort by field
                limit :: Size of each page
                page :: Page number or cursor string
        :return : List of candidates present in list (smart list or dumb list)
        :rtype: json
        """
        smartlist_id = kwargs.get('smartlist_id')
        smartlist = Smartlist.query.get(smartlist_id)
        if not smartlist or smartlist.is_hidden:
            raise NotFoundError("List id does not exists.")

        # check whether smartlist belongs to user's domain
        if smartlist.user.domain_id != request.user.domain_id:
            raise ForbiddenError("Provided list does not belong to user's domain")

        request_params = dict()
        request_params['fields'] = request.args.get('fields', '')
        request_params['sort_by'] = request.args.get('sort_by', '')
        request_params['limit'] = request.args.get('limit', '')
        request_params['page'] = request.args.get('page', '')

        return get_smartlist_candidates(smartlist, request.oauth_token, request_params)


class SmartlistResource(Resource):
    decorators = [require_oauth()]

    def get(self, **kwargs):
        """Retrieve list information
        List must belong to auth user's domain
        Call this resource from url:
            /v1/smartlists?page=1&page_size=10 :: to retrieve all the smartlists in user's domain
            /v1/smartlists/<int:id> :: to get single smartlist

        example: http://localhost:8008/v1/smartlists/2
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
            if not smartlist or smartlist.is_hidden:
                raise NotFoundError("List id does not exists")
            # check whether smartlist belongs to user's domain
            if smartlist.user.domain_id != auth_user.domain_id:
                raise ForbiddenError("List does not belong to user's domain")
            return {'smartlist': create_smartlist_dict(smartlist, request.oauth_token)}
        else:
            # Return all smartlists from user's domain
            page = request.args.get('page', DEFAULT_PAGE)
            per_page = request.args.get('per_page', DEFAULT_PAGE_SIZE)
            total_number_of_smartlists = Smartlist.query.join(Smartlist.user).filter(
                    User.domain_id == auth_user.domain_id, Smartlist.is_hidden == 0).count()

            if not is_number(page) or not is_number(per_page) or int(page) < 1 or int(per_page) < 1:
                raise InvalidUsage("page and per_page should be positive integers")

            page = int(page)
            per_page = int(per_page)

            return {'smartlists': get_all_smartlists(auth_user, request.oauth_token, int(page), int(per_page)),
                    'page_number': page, 'smartlists_per_page': per_page,
                    'total_number_of_smartlists': total_number_of_smartlists}

    def post(self):
        """
        Creates list with search params or with list of candidate ids
        Input data:
            json body having following keys
            "name": Name with which smart list will be created
            "search_params": search parameters for smart list in dictionary format
                or  "candidate_ids": if not search_params then candidate_ids should be present
        :return: smartlist id
        """
        auth_user = request.user
        data = request.get_json(silent=True)
        if not data:
            raise InvalidUsage("Received empty request body")
        # request data must pass through this function, as this will create data in desired format
        data = validate_and_format_smartlist_post_data(data, auth_user)
        smartlist = save_smartlist(user_id=auth_user.id, name=data.get('name'),
                                   talent_pipeline_id=data.get('talent_pipeline_id'),
                                   search_params=data.get('search_params'), candidate_ids=data.get('candidate_ids'),
                                   access_token=request.oauth_token)
        return {'smartlist': {'id': smartlist.id}}, 201

    def delete(self, **kwargs):
        """
        Deletes (hides) the smartlist

        :return: Id of deleted smartlist.
        """
        list_id = kwargs.get('id')
        if not list_id:
            return InvalidUsage("List id is required for deleting a list")

        smartlist = Smartlist.query.get(list_id)
        if not smartlist or smartlist.is_hidden:
            raise NotFoundError("List id does not exists")
        # check whether smartlist belongs to user's domain
        if smartlist.user.domain_id != request.user.domain_id:
            raise ForbiddenError("List does not belong to user's domain")
        smartlist.delete()
        return {'smartlist': {'id': smartlist.id}}


@smartlist_blueprint.route(CandidatePoolApi.SMARTLIST_GET_STATS, methods=['GET'])
@require_oauth(allow_null_user=True)
def get_smartlist_stats(smartlist_id):
    """
    This method will return the statistics of a smartlist over a given period of time with time-period = 1 day
    :param smartlist_id: Id of a smartlist
    :return: A list of time-series data
    """

    smartlist = Smartlist.query.get(smartlist_id)
    from_date_string = request.args.get('from_date', '')
    to_date_string = request.args.get('to_date', '')
    interval = request.args.get('interval', '1')
    offset = request.args.get('offset', 0)

    response = get_stats_generic_function(smartlist, 'SmartList', request.user, from_date_string,
                                          to_date_string, interval, False, offset)
    if 'is_update' in request.args:
        return '', 204
    else:
        return jsonify({'smartlist_data': response})


api = TalentApi(smartlist_blueprint)
api.add_resource(SmartlistResource, CandidatePoolApi.SMARTLIST, CandidatePoolApi.SMARTLISTS)
api.add_resource(SmartlistCandidates,CandidatePoolApi.SMARTLIST_CANDIDATES)

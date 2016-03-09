from dateutil.parser import parse
from datetime import datetime, timedelta
from flask_restful import Resource
from flask import request, Blueprint, jsonify
from candidate_pool_service.common.routes import CandidatePoolApi
from candidate_pool_service.common.talent_api import TalentApi
from candidate_pool_service.common.utils.validators import is_number
from candidate_pool_service.candidate_pool_app import logger
from candidate_pool_service.common.models.user import User
from candidate_pool_service.common.models.smartlist import db, Smartlist, SmartlistStats
from candidate_pool_service.common.utils.auth_utils import require_oauth
from candidate_pool_service.common.error_handling import ForbiddenError, NotFoundError, InvalidUsage
from candidate_pool_service.modules.smartlists import (get_candidates, create_smartlist_dict,
                                                       save_smartlist, get_all_smartlists)
from candidate_pool_service.modules.validators import (validate_and_parse_request_data,
                                                       validate_and_format_smartlist_post_data)
from candidate_pool_service.candidate_pool_app.talent_pools_pipelines_utilities import update_smartlists_stats_task

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
                        `candidate_ids_only` --> returns candidate ids only
                        `count_only` --> returns only the count of candidates present in list
                        `all_fields`  --> returns all candidates' fields (all attributes)
                        'fields' parameter not present --> same as 'all' parameter --> returns all candidate fields
        :return : List of candidates present in list (smart list or dumb list)
        :rtype: json
        """
        smartlist_id = kwargs['smartlist_id']
        data = validate_and_parse_request_data(request.args)
        smartlist = Smartlist.query.get(smartlist_id)
        if not smartlist or smartlist.is_hidden:
            raise NotFoundError("List id does not exists.")
        # check whether smartlist belongs to user's domain
        if smartlist.user.domain_id != request.user.domain_id:
            raise ForbiddenError("Provided list does not belong to user's domain")
        return get_candidates(smartlist, data['candidate_ids_only'], data['count_only'], oauth_token=request.oauth_token)


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
            page = request.args.get('page', 1)
            per_page = request.args.get('per_page', 10)
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
        smartlist = save_smartlist(user_id=auth_user.id, name=data.get('name'), search_params=data.get('search_params'),
                                   candidate_ids=data.get('candidate_ids'), access_token=request.oauth_token)
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


@smartlist_blueprint.route(CandidatePoolApi.SMARTLIST_UPDATE_STATS, methods=['POST'])
@require_oauth(allow_null_user=True)
def update_smartlists_stats():
    """
    This method will update the statistics of all smartlists daily.
    :return: None
    """
    logger.info("SmartLists statistics update process has been started")
    update_smartlists_stats_task.delay()
    return '', 204


@smartlist_blueprint.route(CandidatePoolApi.SMARTLIST_GET_STATS, methods=['GET'])
@require_oauth()
def get_smartlist_stats(smartlist_id):
    """
    This method will return the statistics of a smartlist over a given period of time with time-period = 1 day
    :param smartlist_id: Id of a smartlist
    :return: A list of time-series data
    """
    smartlist = Smartlist.query.get(smartlist_id)

    if not smartlist:
        raise NotFoundError(error_message="SmartList with id=%s doesn't exist in database" % smartlist_id)

    if smartlist.user.domain_id != request.user.domain_id:
        raise ForbiddenError(error_message="Logged-in user %s is unauthorized to get stats of smartlist %s"
                                           % (request.user.id, smartlist.id))

    from_date_string = request.args.get('from_date', '')
    to_date_string = request.args.get('to_date', '')
    interval = request.args.get('interval', '1')

    try:
        from_date = parse(from_date_string) if from_date_string else datetime.fromtimestamp(0)
        to_date = parse(to_date_string) if to_date_string else datetime.utcnow()
    except Exception as e:
        raise InvalidUsage(error_message="Either 'from_date' or 'to_date' is invalid because: %s" % e.message)

    if not is_number(interval):
        raise InvalidUsage("Interval '%s' should be integer" % interval)

    interval = int(interval)
    if interval < 1:
        raise InvalidUsage("Interval's value should be greater than or equal to 1 day")

    smartlist_stats = SmartlistStats.query.filter(SmartlistStats.smartlist_id == smartlist_id,
                                                  SmartlistStats.added_datetime >= from_date,
                                                  SmartlistStats.added_datetime <= to_date).all()
    smartlist_stats.reverse()

    smartlist_stats = smartlist_stats[::interval]

    # Computing number_of_candidates_added by subtracting candidate count of previous day from candidate
    # count of current_day
    smartlist_stats = map(lambda (i, smart_list_stat): {
        'total_number_of_candidates': smart_list_stat.total_number_of_candidates,
        'number_of_candidates_added': (smart_list_stat.total_number_of_candidates - (
            smartlist_stats[i + 1].total_number_of_candidates if i + 1 < len(smartlist_stats) else
            smart_list_stat.total_number_of_candidates)),
        'added_datetime': smart_list_stat.added_datetime.isoformat(),
        'candidates_engagement': smart_list_stat.candidates_engagement
    }, enumerate(smartlist_stats))

    return jsonify({'smartlist_data': smartlist_stats})


api = TalentApi(smartlist_blueprint)
api.add_resource(SmartlistResource, CandidatePoolApi.SMARTLIST, CandidatePoolApi.SMARTLISTS)
api.add_resource(SmartlistCandidates,CandidatePoolApi.SMARTLIST_CANDIDATES)

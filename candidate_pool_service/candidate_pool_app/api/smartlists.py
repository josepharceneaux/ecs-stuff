from dateutil.parser import parse
from datetime import datetime, timedelta
from flask_restful import Resource
from flask import request, Blueprint, jsonify
from candidate_pool_service.common.talent_api import TalentApi
from candidate_pool_service.candidate_pool_app import logger
from candidate_pool_service.common.models.email_marketing import EmailCampaignSend
from candidate_pool_service.common.utils.talent_reporting import email_error_to_admins
from candidate_pool_service.common.models.smartlist import db, Smartlist, SmartlistStats
from candidate_pool_service.common.utils.auth_utils import require_oauth, require_all_roles
from candidate_pool_service.common.error_handling import ForbiddenError, NotFoundError, InvalidUsage
from candidate_pool_service.modules.smartlists import (get_candidates, create_smartlist_dict,
                                                       save_smartlist, get_all_smartlists)
from candidate_pool_service.modules.validators import (validate_and_parse_request_data,
                                                       validate_and_format_smartlist_post_data)

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
        return get_candidates(smartlist, data['candidate_ids_only'], data['count_only'])


class SmartlistResource(Resource):
    decorators = [require_oauth()]

    def get(self, **kwargs):
        """Retrieve list information
        List must belong to auth user's domain
        Call this resource from url: /v1/smartlists :: to retrieve all the smartlists in user's domain
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
            return {'smartlists': get_all_smartlists(auth_user, request.oauth_token)}

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


@smartlist_blueprint.route('/smartlists/stats', methods=['POST'])
@require_oauth(allow_jwt_based_auth=True, allow_null_user=True)
@require_all_roles('CAN_UPDATE_SMARTLISTS_STATS')
def update_smartlists_stats():
    """
    This method will update the statistics of all smartlists daily.
    :return: None
    """
    smartlists = Smartlist.query.all()

    # 2 hours are added to account for scheduled job run time
    yesterday_datetime = datetime.utcnow() - timedelta(days=1, hours=2)

    for smartlist in smartlists:

        try:
            yesterday_stat = SmartlistStats.query.filter(SmartlistStats.smartlist_id == smartlist.id,
                                                        SmartlistStats.added_datetime > yesterday_datetime).first()

            # Return only candidate_ids
            response = get_candidates(smartlist, candidate_ids_only=True)
            total_candidates = response.get('total_found')
            smartlist_candidate_ids = [candidate.get('id') for candidate in response.get('candidates')]

            number_of_engaged_candidates = 0
            if smartlist_candidate_ids:
                number_of_engaged_candidates = db.session.query(EmailCampaignSend.candidate_id).filter(
                        EmailCampaignSend.candidate_id.in_(smartlist_candidate_ids)).count()

            percentage_candidates_engagement = int(float(number_of_engaged_candidates)/total_candidates*100) \
                if int(total_candidates) else 0
            # TODO: SMS_CAMPAIGNS are not implemented yet so we need to integrate them too here.

            if yesterday_stat:
                smartlist_stat = SmartlistStats(smartlist_id=smartlist.id,
                                                total_candidates=total_candidates,
                                                number_of_candidates_removed_or_added=
                                                total_candidates - yesterday_stat.total_candidates,
                                                candidates_engagement=percentage_candidates_engagement)
            else:
                smartlist_stat = SmartlistStats(smartlist_id=smartlist.id,
                                                total_candidates=total_candidates,
                                                number_of_candidates_removed_or_added=total_candidates,
                                                candidates_engagement=percentage_candidates_engagement)
            db.session.add(smartlist_stat)
            db.session.commit()

        except Exception as e:
            db.session.rollback()
            logger.exception("An exception occured update statistics of SmartLists because: %s" % e.message)

    return '', 204


@smartlist_blueprint.route('/smartlists/<int:smartlist_id>/stats', methods=['GET'])
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

    if smartlist.user_id != request.user.id:
        raise ForbiddenError(error_message="Logged-in user %s is unauthorized to get stats of smartlist %s"
                                           % (request.user.id, smartlist.id))

    from_date_string = request.args.get('from_date', '')
    to_date_string = request.args.get('to_date', '')

    if not from_date_string or not to_date_string:
        raise InvalidUsage(error_message="Either 'from_date' or 'to_date' is missing from request parameters")

    try:
        from_date = parse(from_date_string)
        to_date = parse(to_date_string)
    except Exception as e:
        raise InvalidUsage(error_message="Either 'from_date' or 'to_date' is invalid because: %s" % e.message)

    smartlist_stats = SmartlistStats.query.filter(SmartlistStats.smartlist_id == smartlist_id,
                                                  SmartlistStats.added_datetime >= from_date,
                                                  SmartlistStats.added_datetime <= to_date).all()

    return jsonify({'smartlist_data': [
        {
            'total_number_of_candidates': smartlist_stat.total_candidates,
            'number_of_candidates_removed_or_added': smartlist_stat.number_of_candidates_removed_or_added,
            'added_datetime': smartlist_stat.added_datetime,
            'candidates_engagement': smartlist_stat.candidates_engagement
        }
        for smartlist_stat in smartlist_stats
    ]})


api = TalentApi(smartlist_blueprint)
api.add_resource(SmartlistResource, '/smartlists/<int:id>', '/smartlists')
api.add_resource(SmartlistCandidates, '/smartlists/<int:smartlist_id>/candidates')
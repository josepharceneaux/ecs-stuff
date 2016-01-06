__author__ = 'ufarooqi'
import json
import requests
from flask import request
from datetime import datetime, timedelta
from candidate_pool_service.common.models.user import User
from candidate_pool_service.candidate_pool_app import logger, app
from candidate_pool_service.common.redis_cache import redis_store
from candidate_pool_service.common.error_handling import InvalidUsage
from candidate_pool_service.common.models.smartlist import Smartlist
from candidate_pool_service.common.talent_config_manager import TalentConfigKeys
from candidate_pool_service.common.routes import CandidatePoolApiUrl, SchedulerApiUrl, CandidateApiUrl


TALENT_PIPELINE_SEARCH_PARAMS = [
    "query",
    "user_ids",
    "location",
    "radius",
    "area_of_interest_ids",
    "status_ids",
    "source_ids",
    "minimum_years_experience",
    "maximum_years_experience",
    "skills",
    "job_title",
    "school_name",
    "degree_type",
    "major",
    "degree_end_year_from",
    "degree_end_year_to",
    "military_service_status",
    "military_branch",
    "military_highest_grade",
    "military_end_date_from",
    "military_end_date_to"
]


def get_candidates_of_talent_pipeline(talent_pipeline, fields=''):
        """
        Fetch all candidates of a talent-pipeline
        :param talent_pipeline: TalentPipeline Object
        :return: A dict containing info of all candidates according to query parameters
        """

        # Get all smart_lists and dumb_lists of a talent-pipeline
        smart_lists = Smartlist.query.filter_by(talent_pipeline_id=talent_pipeline.id).all()

        search_params, dumb_lists = [], []

        try:
            if talent_pipeline.search_params and json.loads(talent_pipeline.search_params):
                search_params.append(json.loads(talent_pipeline.search_params))
            for smart_list in smart_lists:
                if smart_list.search_params and json.loads(smart_list.search_params):
                    search_params.append(json.loads(smart_list.search_params))
                else:
                    dumb_lists.append(str(smart_list.id))

        except Exception as e:
            raise InvalidUsage(error_message="Search params of talent-pipeline or its smart-lists are in bad format "
                                             "because: %s" % e.message)

        if not request.oauth_token:
            secret_key, oauth_token = User.generate_auth_token(user_id=talent_pipeline.owner_user_id)
            headers = {'Authorization': oauth_token, 'X-Talent-Server-Key': secret_key,
                       'Content-Type': 'application/json'}
        else:
            headers = {'Authorization': request.oauth_token, 'Content-Type': 'application/json'}

        request_params = dict()

        request_params['talent_pool_id'] = talent_pipeline.talent_pool_id
        request_params['fields'] = request.args.get('fields', '') or fields
        request_params['sort_by'] = request.args.get('sort_by', '')
        request_params['limit'] = request.args.get('limit', '')
        request_params['page'] = request.args.get('page', '')
        request_params['dumb_list_ids'] = ','.join(dumb_lists) if dumb_lists else None
        request_params['search_params'] = json.dumps(search_params) if search_params else None

        request_params = dict((k, v) for k, v in request_params.iteritems() if v)

        # Query Candidate Search API to get all candidates of a given talent-pipeline
        try:
            response = requests.get(CandidateApiUrl.CANDIDATE_SEARCH_URI, headers=headers, params=request_params)
            if response.ok:
                return response.json()
            else:
                raise Exception("Status Code: %s, Response: %s" % (response.status_code, response.json()))
        except Exception as e:
            raise InvalidUsage(error_message="Couldn't get candidates from candidates search service because: "
                                             "%s" % e.message)


def schedule_candidate_daily_stats_update():

    env = app.config[TalentConfigKeys.ENV_KEY]

    if not redis_store.get('IS_CANDIDATE_STAT_API_REGISTERED') and env != 'circle':

        data = {
            "frequency": 3600 * 24,  # Daily
            "task_type": "periodic",
            "start_datetime": str(datetime.utcnow() + timedelta(seconds=10)),
            "end_datetime": "2099-01-05T08:00:00",
            "url": CandidatePoolApiUrl.TALENT_POOL_STATS
        }

        secret_key, oauth_token = User.generate_auth_token()
        headers = {'Authorization': oauth_token, 'X-Talent-Server-Key': secret_key, 'Content-Type': 'application/json'}

        try:
            response = requests.post(SchedulerApiUrl.TASKS, headers=headers, data=json.dumps(data))

            if response.status_code != 201:
                raise Exception("Status Code: %s, Response: %s" % (response.status_code, response.json()))

            data['url'] = CandidatePoolApiUrl.TALENT_PIPELINE_STATS
            response = requests.post(SchedulerApiUrl.TASKS, headers=headers, data=json.dumps(data))

            if response.status_code != 201:
                raise Exception("Status Code: %s, Response: %s" % (response.status_code, response.json()))

            data['url'] = CandidatePoolApiUrl.SMARTLIST_STATS
            response = requests.post(SchedulerApiUrl.TASKS, headers=headers, data=json.dumps(data))

            if response.status_code != 201:
                raise Exception("Status Code: %s, Response: %s" % (response.status_code, response.json()))

            redis_store.set('IS_CANDIDATE_STAT_API_REGISTERED', True)

        except Exception as e:
            logger.exception("Couldn't register Candidate statistics update endpoint to Scheduler "
                             "Service because: %s" % e.message)


__author__ = 'ufarooqi'
import json
import decimal
import requests
from flask import request
from dateutil.parser import parse
from celery.schedules import crontab
from datetime import datetime, timedelta, date
from candidate_pool_service.common.utils.validators import is_number
from candidate_pool_service.candidate_pool_app import logger, app, celery_app, db
from candidate_pool_service.common.redis_cache import redis_dict, redis_store
from candidate_pool_service.modules.smartlists import get_candidates
from candidate_pool_service.common.error_handling import InvalidUsage, NotFoundError, ForbiddenError
from candidate_pool_service.common.models.smartlist import Smartlist
from candidate_pool_service.common.models.talent_pools_pipelines import TalentPipeline, TalentPool, User
from candidate_pool_service.common.routes import CandidatePoolApiUrl, CandidateApiUrl

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

SCHEDULER_SERVICE_RESPONSE_CODE_TASK_ALREADY_SCHEDULED = 6057


def generate_jwt_header(oauth_token=None, user_id=None):
    """
    This methid will generate JWT based Auth Header
    :param oauth_token: OAuth2.0 based token i.e. Bearer sdhdfvjsdfbjfgksfbjsdfgjsdhf
    :param user_id: ID of a user
    :return:
    """

    if not oauth_token:
        secret_key, oauth_token = User.generate_jw_token(user_id=user_id)
        headers = {'Authorization': oauth_token, 'X-Talent-Secret-Key-ID': secret_key,
                   'Content-Type': 'application/json'}
    else:
        headers = {'Authorization': oauth_token, 'Content-Type': 'application/json'}

    return headers


def get_candidates_from_search_api(query_string, headers):
    """
    This function will get candidates information based on query_string from Search API
    :param query_string: Query String
    :param headers: Header dictionary
    :return:
    """

    response = requests.get(CandidateApiUrl.CANDIDATE_SEARCH_URI, headers=headers, params=query_string)
    if response.ok:
        return True, response.json()
    else:
        return False, response


def get_pipeline_growth(talent_pipeline, interval):
    """
    This endpoint will return growth in talent-pipeline for given interval size
    :param talent_pipeline: TalentPipeline object
    :param interval: Interval in days
    :return:
    """
    from_date = datetime.utcnow() - timedelta(days=interval)
    return get_talent_pipeline_stat_for_given_day(talent_pipeline, datetime.utcnow().date()) - \
           get_talent_pipeline_stat_for_given_day(talent_pipeline, from_date.date())


def get_smartlist_stat_for_a_given_day(smartlist, date_object):
    """
    This method will get and update smartlist stats for a given day
    :param smartlist: SmartList Object
    :param date_object: DateTime Object
    :return:
    """
    epoch_time_string = '12/31/1969'
    smartlists_growth_stats_dict = redis_dict(redis_store, 'smartlists_growth_stat_%s' % smartlist.id)
    # If date_object is before smartlist creation date then we don't need to store statistics information in Database
    if date_object < smartlist.added_time.date():
        return 0
    else:
        date_string = date_object.strftime('%m/%d/%Y')
        if date_string not in smartlists_growth_stats_dict:
            # Get SmartList Candidates Using Search API
            response = get_candidates(smartlist, False, True, None)
            smartlists_growth_stats_dict[date_string] = response.get('total_found')

        return smartlists_growth_stats_dict[date_string]


def get_talent_pipeline_stat_for_given_day(talent_pipeline, date_object):
    """
    This method will get and update talent-pipeline stats for a given day
    :param talent_pipeline: TalentPipeline Object
    :param date_object: DateTime Object
    :return:
    """
    epoch_time_string = '12/31/1969'
    pipelines_growth_stats_dict = redis_dict(redis_store, 'pipelines_growth_stat_%s' % talent_pipeline.id)
    # If date_object is before talent-pipeline creation date then we don't need to store statistics information in Database
    if date_object < talent_pipeline.added_time.date():
        return 0
    else:
        date_string = date_object.strftime('%m/%d/%Y')
        if date_string not in pipelines_growth_stats_dict:
            # Get Talent Pipeline Candidates Using Search API
            response = get_candidates_of_talent_pipeline(talent_pipeline, fields='count_only', request_params={
                'date_from': epoch_time_string, 'date_to': date_string})
            pipelines_growth_stats_dict[date_string] = response.get('total_found')

        return pipelines_growth_stats_dict[date_string]


def get_talent_pool_stat_for_a_given_day(talent_pool, date_object):
    """
    This method will get and update talent-pool stats for a given day
    :param talent_pool: TalentPool Object
    :param date_object: DateTime Object
    :return:
    """
    epoch_time_string = '12/31/1969'
    pools_growth_stats_dict = redis_dict(redis_store, 'pools_growth_stat_%s' % talent_pool.id)

    # If date_object is before talent-pool creation date then we don't need to store statistics information in Database
    if date_object < talent_pool.added_time.date():
        return 0
    else:
        date_string = date_object.strftime('%m/%d/%Y')
        if date_string not in pools_growth_stats_dict:
            # Get Talent Pool Candidates Using Search API
            query_parameters = {'talent_pool_id': talent_pool.id, 'fields':'count_only',
                                'date_from': epoch_time_string, 'date_to': date_string}
            headers = generate_jwt_header(request.oauth_token, talent_pool.user_id)
            is_successful, response = get_candidates_from_search_api(query_parameters, headers)

            if not is_successful:
                raise NotFoundError("TalentPoolStatistics: Couldn't get candidates from candidates search "
                                    "service because: %s" % response)
            else:
                pools_growth_stats_dict[date_string] = response.get('total_found')

        return pools_growth_stats_dict[date_string]


def get_candidates_of_talent_pipeline(talent_pipeline, fields='', oauth_token=None, is_celery_task=False,
                                      request_params=None):
    """
        Fetch all candidates of a talent-pipeline
        :param talent_pipeline: TalentPipeline Object
        :param fields: Return fields
        :param oauth_token: Authorization Token
        :param is_celery_task: Is this method is called by a celery task or not
        :param request_params: Request parameters
        :return: A dict containing info of all candidates according to query parameters
        """

    # Get all smartlists and dumblists of a talent-pipeline
    smartlists = Smartlist.query.filter_by(talent_pipeline_id=talent_pipeline.id).all()

    smartlist_ids, dumblist_ids = [], []

    if request_params is None:
        request_params = dict()

    try:
        if talent_pipeline.search_params:
            request_params.update(json.loads(talent_pipeline.search_params))

        for smartlist in smartlists:
            if smartlist.search_params and json.loads(smartlist.search_params):
                smartlist_ids.append(str(smartlist.id))
            else:
                dumblist_ids.append(str(smartlist.id))

    except Exception as e:
        raise InvalidUsage(error_message="Search params of talent pipeline or its smartlists are in bad format "
                                         "because: %s" % e.message)

    if not is_celery_task:
        request_params['fields'] = request.args.get('fields', '') or fields
        request_params['sort_by'] = request.args.get('sort_by', '')
        request_params['limit'] = request.args.get('limit', '')
        request_params['page'] = request.args.get('page', '')
    else:
        request_params['fields'] = fields

    request_params['talent_pool_id'] = talent_pipeline.talent_pool_id
    request_params['dumb_list_ids'] = ','.join(dumblist_ids) if dumblist_ids else None
    request_params['smartlist_ids'] = ','.join(smartlist_ids) if smartlist_ids else None

    request_params = dict((k, v) for k, v in request_params.iteritems() if v)

    # Query Candidate Search API to get all candidates of a given talent-pipeline
    is_successful, response = get_candidates_from_search_api(request_params,
                                                             generate_jwt_header(oauth_token, talent_pipeline.user_id))

    if not is_successful:
        if is_celery_task:
            logger.exception("Couldn't get candidates from candidates search service because: %s" % response)
            return False
        else:
            raise NotFoundError("Couldn't get candidates from candidates search service because: %s" % response)
    else:
        return response


def campaign_json_encoder_helper(obj):
    """JSON encoder function for SQLAlchemy special classes."""
    if isinstance(obj, date):
        return obj.isoformat()
    elif isinstance(obj, decimal.Decimal):
        return float(obj)


@celery_app.task(name="update_talent_pool_stats")
def update_talent_pool_stats():
    with app.app_context():
        # Updating TalentPool Statistics
        logger.info("TalentPool statistics update process has been started at %s" % datetime.utcnow().date().isoformat())
        talent_pools = TalentPool.query.with_entities(TalentPool.id).all()
        try:
            for talent_pool_tuple in talent_pools:
                response = requests.get(CandidatePoolApiUrl.TALENT_POOL_GET_STATS % talent_pool_tuple[0],
                                        headers=generate_jwt_header(), params=dict(is_update=1))
                if response.status_code == 204:
                    logger.info("Statistics for TalentPool %s have been updated successfully" % talent_pool_tuple[0])
                else:
                    logger.exception("Update statistics for TalentPool %s is not successful" % talent_pool_tuple[0])
        except Exception as e:
            logger.exception("An Exception occurs while updating TalentPipeline Statistics because: %s" % e.message)
        talent_pool_ids = map(lambda talent_pool: talent_pool[0], talent_pools)
        delete_dangling_stats(talent_pool_ids, container='talent-pool')


@celery_app.task(name="update_talent_pipeline_stats")
def update_talent_pipeline_stats():
    with app.app_context():
        # Updating TalentPipeline Statistics
        logger.info("TalentPipeline statistics update process has been started at %s" % datetime.utcnow().date().isoformat())
        talent_pipelines = TalentPipeline.query.with_entities(TalentPipeline.id).all()
        try:
            for talent_pipeline_tuple in talent_pipelines:
                response = requests.get(CandidatePoolApiUrl.TALENT_PIPELINE_GET_STATS % talent_pipeline_tuple[0],
                                        headers=generate_jwt_header(), params=dict(is_update=1))
                if response.status_code == 204:
                    logger.info("Statistics for TalentPipeline %s have been updated successfully" % talent_pipeline_tuple[0])
                else:
                    logger.exception("Update statistics for TalentPipeline %s is not successful" % talent_pipeline_tuple[0])
        except Exception as e:
            logger.exception("An Exception occurs while updating TalentPipeline Statistics because: %s" % e.message)
        talent_pipeline_ids = map(lambda talent_pipeline: talent_pipeline[0], talent_pipelines)
        delete_dangling_stats(talent_pipeline_ids, container='talent-pipeline')


@celery_app.task(name="update_smartlist_stats")
def update_smartlist_stats():
    with app.app_context():
        # Updating SmartList Statistics
        logger.info("SmartList statistics update process has been started at %s" % datetime.utcnow().date().isoformat())
        smartlists = Smartlist.query.with_entities(Smartlist.id).all()
        try:
            for smartlist_tuple in smartlists:
                response = requests.get(CandidatePoolApiUrl.SMARTLIST_GET_STATS % smartlist_tuple[0],
                                        headers=generate_jwt_header(), params=dict(is_update=1))
                if response.status_code == 204:
                    logger.info("Statistics for Smartlist %s have been updated successfully" % smartlist_tuple[0])
                else:
                    logger.exception("Update statistics for SmartList %s is not successful" % smartlist_tuple[0])
        except Exception as e:
            logger.exception("An Exception occurs while updating SmartList Statistics because: %s" % e.message)

        smartlist_ids = map(lambda smartlist: smartlist[0], smartlists)
        delete_dangling_stats(smartlist_ids, container='smartlist')


def schedule_candidate_daily_stats_update():

    celery_app.conf.update({'CELERYBEAT_SCHEDULE': {
        'update_talent_pipeline_stats': {
            'task': 'update_talent_pipeline_stats',
            'schedule': crontab(minute=0, hour=0),  # Daily at Midnight
        },
        'update_talent_pool_stats': {
            'task': 'update_talent_pool_stats',
            'schedule': crontab(minute=0, hour=0),  # Daily at Midnight
        },
        'update_smartlist_stats': {
            'task': 'update_smartlist_stats',
            'schedule': crontab(minute=0, hour=0),  # Daily at Midnight
        },

    }})


def delete_dangling_stats(id_list, container):
    """
    This method will delete dangling statistics from Redis for each of three containers
    :param id_list: List of IDs
    :param container: Container's name
    :return:
    """
    if container == 'smartlist':
        redist_key = 'smartlists_growth_stat_'
    elif container == 'talent-pool':
        redist_key = 'pools_growth_stat_'
    elif container == 'talent-pipeline':
        redist_key = 'pipelines_growth_stat_'
    else:
        raise Exception("Container %s is not supported" % container)

    for key in redis_store.keys(redist_key + '*'):
        if int(key.replace(redist_key, '')) not in id_list:
            redis_store.delete(redis_store.get(key))

    logger.info("Dangling Statistics have been deleted for %s" % container)


def get_stats_generic_function(container_object, container_name, user=None, from_date_string='', to_date_string='', interval=1):
    """
    This method will be used to get stats for talent-pools, talent-pipelines or smartlists.
    :param container_object: TalentPipeline, TalentPool or SmartList Object
    :param container_name:
    :param user: Logged-in user
    :param from_date_string: From Date String
    :param to_date_string: To Date String
    :param interval: Interval in days
    :return:
    """
    if not container_object:
        raise NotFoundError("%s with id=%s doesn't exist in database" % (container_name, container_object.id))

    if user and container_object.user.domain_id != user.domain_id:
        raise ForbiddenError("Logged-in user %s is unauthorized to get stats of %s: %s" % (user.id, container_name,
                                                                                           container_object.id))

    try:
        from_date = parse(from_date_string).date() if from_date_string else container_object.added_time.date()
        to_date = parse(to_date_string).date() if to_date_string else datetime.utcnow().date()
    except Exception as e:
        raise InvalidUsage("Either 'from_date' or 'to_date' is invalid because: %s" % e.message)

    if from_date > to_date:
        raise InvalidUsage("`to_date` cannot come before `from_date`")

    if not is_number(interval):
        raise InvalidUsage("Interval '%s' should be integer" % interval)

    interval = int(interval)
    if interval < 1:
        raise InvalidUsage("Interval's value should be greater than or equal to 1 day")

    if container_name == 'TalentPipeline':
        get_stats_for_given_day = get_talent_pipeline_stat_for_given_day
    elif container_name == 'TalentPool':
        get_stats_for_given_day = get_talent_pool_stat_for_a_given_day
    elif container_name == 'SmartList':
        get_stats_for_given_day = get_smartlist_stat_for_a_given_day
    else:
        raise Exception("Container %s is not supported for this method" % container_name)

    list_of_stats_dicts = []
    while to_date >= from_date:
        list_of_stats_dicts.append({
            'total_number_of_candidates': get_stats_for_given_day(container_object, to_date),
            'added_datetime': to_date.isoformat(),
        })
        to_date -= timedelta(days=interval)

    reference_stat = get_stats_for_given_day(container_object, to_date)
    for index, stat_dict in enumerate(list_of_stats_dicts):
        stat_dict['number_of_candidates_added'] = stat_dict['total_number_of_candidates'] - (
            list_of_stats_dicts[index + 1]['total_number_of_candidates'] if index + 1 < len(
                    list_of_stats_dicts) else reference_stat)

    return list_of_stats_dicts
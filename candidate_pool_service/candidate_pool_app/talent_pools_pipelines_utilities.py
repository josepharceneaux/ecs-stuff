__author__ = 'ufarooqi'
import math
import json
import decimal
import requests
from sqlalchemy.sql import text
from dateutil.parser import parse
from datetime import datetime, timedelta, date
from candidate_pool_service.common.utils.validators import is_number
from candidate_pool_service.candidate_pool_app import logger, app, celery_app, db
from candidate_pool_service.common.redis_cache import redis_dict, redis_store
from candidate_pool_service.common.routes import CandidateApiUrl
from candidate_pool_service.common.models.smartlist import Smartlist
from candidate_pool_service.common.error_handling import InvalidUsage, NotFoundError, ForbiddenError
from candidate_pool_service.common.models.talent_pools_pipelines import TalentPipeline, TalentPool, User, TalentPoolCandidate

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
    "military_end_date_to",
    "skillDescriptionFacet",
    "tag_ids",
    "custom_fields",
    "dumb_list_ids",
    "smartlist_ids",
    "date_to",
    "id",
    "date_from",
    "talent_pool_id"
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
        oauth_token = User.generate_jw_token(user_id=user_id)

    headers = {'Authorization': oauth_token, 'Content-Type': 'application/json'}

    return headers


def get_smartlist_candidates(smartlist, oauth_token=None, request_params=None):
    """
    This endpoint will be used to get smartlist candidates for given duration
    :param search_params: search parameters dict
    :param oauth_token: OAuth Token value
    :return:
    """
    if request_params is None:
        request_params = dict()
    if smartlist.talent_pipeline:
        if smartlist.talent_pipeline.search_params:
            try:
                request_params.update(json.loads(smartlist.talent_pipeline.search_params))
            except Exception as e:
                raise InvalidUsage("Search params of talent pipeline are in bad format because: %s" % e.message)

        request_params['talent_pool_id'] = smartlist.talent_pipeline.talent_pool_id

    if smartlist.search_params:
        request_params['smartlist_ids'] = smartlist.id
    else:
        request_params['dumb_list_ids'] = smartlist.id

    request_params = dict((k, v) for k, v in request_params.iteritems() if v)

    is_successful, response = get_candidates_from_search_api(request_params, generate_jwt_header(oauth_token, smartlist.user_id))
    if not is_successful:
        raise NotFoundError("Couldn't get candidates for smartlist %s" % smartlist.id)
    else:
        return response


def get_candidates_from_search_api(query_string, headers):
    """
    This function will get candidates information based on query_string from Search API
    :param query_string: Query String
    :param headers: Header dictionary
    :return:
    """

    response = requests.get(CandidateApiUrl.CANDIDATE_SEARCH_URI,
                            headers=headers, params=query_string)
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
    if talent_pipeline.added_time.date() == datetime.utcnow().date():
        return 0
    else:
        to_date = datetime.utcnow() - timedelta(days=1)
        from_date = to_date - timedelta(days=interval)
        return get_talent_pipeline_stat_for_given_day(talent_pipeline, to_date) - \
               get_talent_pipeline_stat_for_given_day(talent_pipeline, from_date)


def get_smartlist_stat_for_a_given_day(smartlist, date_object):
    """
    This method will get and update smartlist stats for a given day
    :param smartlist: SmartList Object
    :param date_object: DateTime Object
    :return:
    """
    epoch_time_string = '1969-12-31'
    current_date_time = datetime.utcnow()
    date_string = date_object.strftime('%m/%d/%Y')
    smartlists_growth_stats_dict = redis_dict(redis_store, 'smartlists_growth_stat_v2_%s' % smartlist.id)
    if date_object < smartlist.added_time:
        return 0

    if date_string not in smartlists_growth_stats_dict:
        smartlists_growth_stats_dict[date_string] = redis_dict(redis_store).key

    if date_object.date() >= current_date_time.date():
        response = get_smartlist_candidates(smartlist, request_params={
            'date_from': epoch_time_string, 'date_to': date_object.strftime('%Y-%m-%dT%H:%M:%S'),
            'fields': 'count_only'})
        return response.get('total_found')

    else:
        redis_dictionary_for_hours = redis_dict(redis_store, smartlists_growth_stats_dict[date_string])
        populate_stats_dictionary(redis_dictionary_for_hours, get_smartlist_candidates, smartlist, date_object)

        return redis_dictionary_for_hours[date_object.hour]


def get_talent_pipeline_stat_for_given_day(talent_pipeline, date_object):
    """
    This method will get and update talent-pipeline stats for a given day
    :param talent_pipeline: TalentPipeline Object
    :param date_object: DateTime Object
    :param is_update: Either we are in between daily stats update process
    :return:
    """
    epoch_time_string = '1969-12-31'
    current_date_time = datetime.utcnow()
    date_string = date_object.strftime('%m/%d/%Y')
    pipelines_growth_stats_dict = redis_dict(redis_store, 'pipelines_growth_stat_v2_%s' % talent_pipeline.id)
    if date_object < talent_pipeline.added_time:
        return 0

    if date_string not in pipelines_growth_stats_dict:
        pipelines_growth_stats_dict[date_string] = redis_dict(redis_store).key

    if date_object.date() >= current_date_time.date():
        response = get_candidates_of_talent_pipeline(talent_pipeline, request_params={
            'date_from': epoch_time_string, 'date_to': date_object.strftime('%Y-%m-%dT%H:%M:%S'),
            'fields': 'count_only'})
        return response.get('total_found')

    else:
        redis_dictionary_for_hours = redis_dict(redis_store, pipelines_growth_stats_dict[date_string])
        populate_stats_dictionary(redis_dictionary_for_hours, get_candidates_of_talent_pipeline,
                                  talent_pipeline, date_object)

        return redis_dictionary_for_hours[date_object.hour]


def get_talent_pool_stat_for_a_given_day(talent_pool, date_object):
    """
    This method will get and update talent-pool stats for a given day
    :param talent_pool: TalentPool Object
    :param date_object: DateTime Object
    :return:
    """
    epoch_time_string = '1969-12-31'
    current_date_time = datetime.utcnow()
    date_string = date_object.strftime('%m/%d/%Y')
    pools_growth_stats_dict = redis_dict(redis_store, 'pools_growth_stat_v2_%s' % talent_pool.id)
    if date_object < talent_pool.added_time:
        return 0

    if date_string not in pools_growth_stats_dict:
        pools_growth_stats_dict[date_string] = redis_dict(redis_store).key

    if date_object.date() >= current_date_time.date():
        response = get_candidates_of_talent_pool(talent_pool, request_params={
            'date_from': epoch_time_string, 'date_to': date_object.strftime('%Y-%m-%dT%H:%M:%S'),
            'fields': 'count_only'})
        return response.get('total_found')

    else:
        redis_dictionary_for_hours = redis_dict(redis_store, pools_growth_stats_dict[date_string])
        populate_stats_dictionary(redis_dictionary_for_hours, get_candidates_of_talent_pool, talent_pool, date_object)

        return redis_dictionary_for_hours[date_object.hour]


def populate_stats_dictionary(stats_redis_object, get_candidates_function, container_object, date_object):
    """
    This method will populate stats_redis_object using get_candidates_function
    :param stats_redis_object: Redis Collection object
    :param get_candidates_function: function to get candidates from cloud search
    :param container_object: Container object like talent_pipeline or talent_pool
    :param date_object: DateTime object
    :return:
    """
    if len(stats_redis_object.keys()) != 24:
        response = get_candidates_function(container_object, request_params={
            'date_from': '12/31/1969',
            'date_to': (date_object - timedelta(days=1)).replace(hour=23, minute=59, second=59).strftime('%Y-%m-%dT%H:%M:%S'),
            'fields': 'count_only'
        })
        total_number_of_candidates_on_last_day = response.get('total_found')
        response = get_candidates_function(container_object, request_params={
            'date_from': date_object.replace(hour=0, minute=0, second=0, microsecond=0).strftime('%Y-%m-%dT%H:%M:%S'),
            'date_to': date_object.replace(hour=23, minute=59, second=59).strftime('%Y-%m-%dT%H:%M:%S'),
            'fields': 'count_only'
        })
        added_time_hour_facet = response.get('facets').get('added_time_hour')
        for index, count in enumerate(added_time_hour_facet):
            if index - 1 >= 0:
                stats_redis_object[index] = count + stats_redis_object[index - 1]
            else:
                stats_redis_object[index] = total_number_of_candidates_on_last_day


def get_candidates_of_talent_pool(talent_pool, oauth_token=None, request_params=None):
    """
    Fetch all candidates of a talent-pool
    :param talent_pool: TalentPool Object
    :param oauth_token: Authorization Token
    :param request_params: Request parameters
    :return: A dict containing info of all candidates according to query parameters
    """
    if request_params is None:
        request_params = dict()
    else:
        request_params['talent_pool_id'] = talent_pool.id

    request_params = dict((k, v) for k, v in request_params.iteritems() if v)

    # Query Candidate Search API to get all candidates of a given talent-pipeline
    is_successful, response = get_candidates_from_search_api(request_params,
                                                             generate_jwt_header(oauth_token, talent_pool.user_id))

    if not is_successful:
        raise NotFoundError("Couldn't get candidates from candidates search service because: %s" % response)
    else:
        return response


def get_candidates_of_talent_pipeline(talent_pipeline, oauth_token=None, request_params=None):
    """
    Fetch all candidates of a talent-pipeline
    :param talent_pipeline: TalentPipeline Object
    :param oauth_token: Authorization Token
    :param request_params: Request parameters
    :return: A dict containing info of all candidates according to query parameters
    """

    if request_params is None:
        request_params = dict()

    try:
        if talent_pipeline.search_params:
            request_params.update(json.loads(talent_pipeline.search_params))

    except Exception as e:
        raise InvalidUsage(error_message="Search params of talent pipeline or its smartlists are in bad format "
                                         "because: %s" % e.message)

    request_params['talent_pool_id'] = talent_pipeline.talent_pool_id

    request_params = dict((k, v) for k, v in request_params.iteritems() if v)

    # Query Candidate Search API to get all candidates of a given talent-pipeline
    is_successful, response = get_candidates_from_search_api(request_params,
                                                             generate_jwt_header(oauth_token, talent_pipeline.user_id))

    if not is_successful:
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
        for talent_pool_tuple in talent_pools:
            try:
                get_stats_generic_function(TalentPool.query.get(talent_pool_tuple[0]), 'TalentPool',
                                           is_update=True, offset=0)
                logger.info("Statistics for TalentPool %s have been updated successfully" % talent_pool_tuple[0])
            except Exception as e:
                db.session.rollback()
                logger.exception("Update statistics for TalentPool %s is not successful because: "
                                 "%s" % (talent_pool_tuple[0], e.message))

        talent_pool_ids = map(lambda talent_pool: talent_pool[0], talent_pools)
        delete_dangling_stats(talent_pool_ids, container='talent-pool')


@celery_app.task(name="update_talent_pipeline_stats")
def update_talent_pipeline_stats():
    with app.app_context():
        # Updating TalentPipeline Statistics
        logger.info("TalentPipeline statistics update process has been started at %s" % datetime.utcnow().isoformat())
        talent_pipelines = TalentPipeline.query.with_entities(TalentPipeline.id).all()
        for talent_pipeline_tuple in talent_pipelines:
            try:
                get_stats_generic_function(TalentPipeline.query.get(talent_pipeline_tuple[0]),
                                           'TalentPipeline', is_update=True, offset=0)
                logger.info("Statistics for TalentPipeline %s have been updated successfully" % talent_pipeline_tuple[0])
            except Exception as e:
                db.session.rollback()
                logger.exception("Update statistics for TalentPipeline %s is not successful because: "
                                 "%s" % (talent_pipeline_tuple[0], e.message))

        talent_pipeline_ids = map(lambda talent_pipeline: talent_pipeline[0], talent_pipelines)
        delete_dangling_stats(talent_pipeline_ids, container='talent-pipeline')


@celery_app.task(name="update_smartlist_stats")
def update_smartlist_stats():
    with app.app_context():
        # Updating SmartList Statistics
        logger.info("SmartList statistics update process has been started at %s" % datetime.utcnow().date().isoformat())
        smartlists = Smartlist.query.with_entities(Smartlist.id).all()
        for smartlist_tuple in smartlists:
            try:
                get_stats_generic_function(Smartlist.query.get(smartlist_tuple[0]), 'SmartList',
                                           is_update=True, offset=0)
                logger.info("Statistics for Smartlist %s have been updated successfully" % smartlist_tuple[0])
            except Exception as e:
                db.session.rollback()
                logger.exception("Update statistics for SmartList %s is not successful because: "
                                 "%s" % (smartlist_tuple[0], e.message))

        smartlist_ids = map(lambda smartlist: smartlist[0], smartlists)
        delete_dangling_stats(smartlist_ids, container='smartlist')


def delete_all_stats(container, container_id):
    """
    This method will delete all statistics from Redis for each of three containers
    :param container: Container's name
    :return:
    """
    if container == 'smartlist':
        redis_key = 'smartlists_growth_stat_v2_'
    elif container == 'talent-pool':
        redis_key = 'pools_growth_stat_v2_'
    elif container == 'talent-pipeline':
        redis_key = 'pipelines_growth_stat_v2_'
    else:
        raise Exception("Container %s is not supported" % container)

    key = redis_key + str(container_id)
    redis_store.delete(redis_store.get(key))
    redis_store.delete(key)


def delete_dangling_stats(id_list, container):
    """
    This method will delete dangling statistics from Redis for each of three containers
    :param id_list: List of IDs
    :param container: Container's name
    :return:
    """
    if container == 'smartlist':
        redist_key = 'smartlists_growth_stat_v2_'
    elif container == 'talent-pool':
        redist_key = 'pools_growth_stat_v2_'
    elif container == 'talent-pipeline':
        redist_key = 'pipelines_growth_stat_v2_'
    else:
        raise Exception("Container %s is not supported" % container)

    for key in redis_store.keys(redist_key + '*'):
        hashed_key = redis_store.get(key)
        if int(key.replace(redist_key, '')) not in id_list:
            redis_store.delete(hashed_key)
            redis_store.delete(key)
        else:
            # Delete all stats which are older than 90 days
            for date_time_key in redis_store.hkeys(hashed_key):
                if datetime.strptime(date_time_key, '%m/%d/%Y') < datetime.utcnow() - timedelta(days=90):
                    redis_store.delete(redis_store.hget(hashed_key, date_time_key))
                    redis_store.hdel(hashed_key, date_time_key)

    logger.info("Dangling Statistics have been deleted for %s" % container)


def get_stats_generic_function(container_object, container_name, user=None, from_date_string='',
                               to_date_string='', interval=1, is_update=False, offset=0):
    """
    This method will be used to get stats for talent-pools, talent-pipelines or smartlists.
    :param container_object: TalentPipeline, TalentPool or SmartList Object
    :param container_name:
    :param user: Logged-in user
    :param from_date_string: From Date String (In Client's Local TimeZone)
    :param to_date_string: To Date String (In Client's Local TimeZone)
    :param interval: Interval in days
    :param is_update: Either stats update process is in progress
    :param offset: Timezone offset from utc i.e. if client's lagging 4 hours behind utc, offset value should be -4
    :return:
    """
    if not container_object:
        raise NotFoundError("%s doesn't exist in database" % container_name)

    if user and container_object.user.domain_id != user.domain_id:
        raise ForbiddenError("Logged-in user %s is unauthorized to get stats of %s: %s" % (user.id, container_name,
                                                                                           container_object.id))

    if not is_number(offset) or math.ceil(abs(float(offset))) > 12:
        raise InvalidUsage("Value of offset should be an integer and less than or equal to 12")

    offset = int(math.ceil(float(offset)))

    current_date_time = datetime.utcnow()

    ninety_days_old_date_time = current_date_time - timedelta(days=90)

    try:
        # To convert UTC time to any other time zone we can use `offset_date_time` with inverted value of offset
        from_date = parse(from_date_string).replace(tzinfo=None) if from_date_string \
            else offset_date_time(ninety_days_old_date_time, -1 * offset)
        to_date = parse(to_date_string).replace(tzinfo=None) if to_date_string else \
            offset_date_time(current_date_time, -1 * offset)
    except Exception as e:
        raise InvalidUsage("Either 'from_date' or 'to_date' is invalid because: %s" % e.message)

    if offset_date_time(from_date, offset) < container_object.added_time:
        from_date = offset_date_time(container_object.added_time, -1 * offset)

    if offset_date_time(from_date, offset) < ninety_days_old_date_time:
        raise InvalidUsage("`Stats data older than 90 days cannot be retrieved`")

    if from_date > to_date:
        raise InvalidUsage("`to_date` cannot come before `from_date`")

    if offset_date_time(to_date, offset) > current_date_time:
        raise InvalidUsage("`to_date` cannot be in future")

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

    to_date = to_date.replace(hour=23, minute=59, second=59)
    from_date = from_date.replace(hour=23, minute=59, second=59)

    if is_update:
        to_date -= timedelta(days=interval)

    while to_date.date() >= from_date.date():
        list_of_stats_dicts.append({
            'total_number_of_candidates': get_stats_for_given_day(
                    container_object, offset_date_time(to_date, offset)),
            'added_datetime': to_date.date().isoformat(),
        })
        to_date -= timedelta(days=interval)

    reference_stat = get_stats_for_given_day(container_object, offset_date_time(to_date, offset))
    for index, stat_dict in enumerate(list_of_stats_dicts):
        stat_dict['number_of_candidates_added'] = stat_dict['total_number_of_candidates'] - (
            list_of_stats_dicts[index + 1]['total_number_of_candidates'] if index + 1 < len(
                    list_of_stats_dicts) else reference_stat)

    return list_of_stats_dicts


def offset_date_time(date_object, offset):
    """
    This method will return new datetime after applying offset
    :param date_object: DateTime Object
    :param offset: Integer in range [-12:12]
    :return:
    """
    return date_object + ((1 if offset < 0 else -1) * timedelta(hours=abs(offset)))


def top_most_engaged_candidates_of_pipeline(talent_pipeline_id, limit):
    """
    This endpoint will return candidate_ids of top most engaged candidates of a talent_pipeline
    :param talent_pipeline_id: Id of talent_pipeline
    :param limit: Number of results returned by this method
    :return: List of candidate Ids of top (limit) most engaged candidates
    :rtype: list
    """

    sql_query = """
    SELECT candidates_engagement_score.CandidateId,
       avg(candidates_engagement_score.campaign_engagement_score) AS engagement_score
    FROM
      (SELECT engagement_score_for_each_sent.CandidateId,
              engagement_score_for_each_sent.EmailCampaignId,
              avg(engagement_score_for_each_sent.engagement_score) AS campaign_engagement_score
       FROM
         (SELECT email_campaign_send.Id,
                 email_campaign_send.EmailCampaignId,
                 email_campaign_send.CandidateId,
                 CASE WHEN sum(url_conversion.HitCount) = 0 THEN 0.0 WHEN sum(email_campaign_send_url_conversion.type * url_conversion.HitCount) > 0 THEN 100 ELSE 33.3 END AS engagement_score
          FROM smart_list
          INNER JOIN email_campaign_smart_list ON smart_list.Id = email_campaign_smart_list.SmartListId
          INNER JOIN email_campaign_send ON email_campaign_send.EmailCampaignId = email_campaign_smart_list.EmailCampaignId
          INNER JOIN email_campaign_send_url_conversion ON email_campaign_send_url_conversion.EmailCampaignSendId = email_campaign_send.Id
          INNER JOIN url_conversion ON email_campaign_send_url_conversion.UrlConversionId = url_conversion.Id
          WHERE smart_list.talentPipelineId = :talent_pipeline_id
          GROUP BY email_campaign_send.Id,
                   email_campaign_send.EmailCampaignId,
                   email_campaign_send.CandidateId) AS engagement_score_for_each_sent
       GROUP BY engagement_score_for_each_sent.EmailCampaignId) AS candidates_engagement_score
    GROUP BY candidates_engagement_score.CandidateId
    ORDER BY engagement_score DESC LIMIT :limit;
    """

    try:
        engagement_scores = db.session.connection().execute(text(sql_query),
                                                            talent_pipeline_id=talent_pipeline_id, limit=limit)
        return [{'candidate_id': engagement_score['CandidateId'], 'engagement_score': float(str(
                engagement_score['engagement_score']))} for engagement_score in engagement_scores]
    except Exception as e:
        logger.exception("Couldn't get top most engaged candidates of talent-pipeline(%s) "
                         "because (%s)" % (talent_pipeline_id, e.message))
        return []


def engagement_score_of_pipeline(talent_pipeline_id):
    """
    This endpoint will calculate engagement_score of a talent_pipeline
    :param talent_pipeline_id: Id of talent_pipeline
    :return: engagement_score of talent_pipeline
    :rtype: list
    """

    sql_query = """
    SELECT avg(pipeline_engagement.campaign_engagement_score) AS pipeline_engagement_score
      FROM
        (SELECT avg(engagement_score_for_each_sent.engagement_score) AS campaign_engagement_score
           FROM
             (SELECT email_campaign_send.Id,
                     email_campaign_send.EmailCampaignId,
                     CASE WHEN sum(url_conversion.HitCount) = 0 THEN 0.0 WHEN sum(email_campaign_send_url_conversion.type * url_conversion.HitCount) > 0 THEN 100 ELSE 33.3 END AS engagement_score
              FROM smart_list
              INNER JOIN email_campaign_smart_list ON smart_list.Id = email_campaign_smart_list.SmartListId
              INNER JOIN email_campaign_send ON email_campaign_send.EmailCampaignId = email_campaign_smart_list.EmailCampaignId
              INNER JOIN email_campaign_send_url_conversion ON email_campaign_send_url_conversion.EmailCampaignSendId = email_campaign_send.Id
              INNER JOIN url_conversion ON email_campaign_send_url_conversion.UrlConversionId = url_conversion.Id
              WHERE smart_list.talentPipelineId = :talent_pipeline_id
              GROUP BY email_campaign_send.Id, email_campaign_send.EmailCampaignId) AS engagement_score_for_each_sent
              GROUP BY engagement_score_for_each_sent.EmailCampaignId) AS pipeline_engagement
    """

    try:
        engagement_score = db.session.connection().execute(text(sql_query), talent_pipeline_id=talent_pipeline_id)
        result = engagement_score.fetchone()
        if not result or not result['pipeline_engagement_score']:
            return None
        else:
            return float(str(result['pipeline_engagement_score']))
    except Exception as e:
        logger.exception("Couldn't compute engagement score for pipeline(%s) because (%s)" % (talent_pipeline_id, e.message))
        return None


def top_most_engaged_pipelines_of_candidate(candidate_id, limit):
    """
    This endpoint will return top most engaged pipelines and their engagement score.
    :param candidate_id: Id of candidate
    :param limit: Number of results to be returned
    :return: List of dicts containing pipeline's id, name and engagement score
    """
    talent_pool_ids_of_candidate = TalentPoolCandidate.query.with_entities(
            TalentPoolCandidate.talent_pool_id).filter(TalentPoolCandidate.candidate_id == candidate_id).all()
    talent_pool_ids_of_candidate = [talent_pool_id_of_candidate.talent_pool_id for
                                    talent_pool_id_of_candidate in talent_pool_ids_of_candidate]

    if not talent_pool_ids_of_candidate:
        talent_pool_ids_of_candidate = ['NULL']

    sql_query = """
      SELECT talent_pipeline.id, talent_pipeline.name, avg(engagement_score_of_all_campaigns.engagement_score) as average_engagement_score_of_pipeline
      FROM
       (SELECT email_campaign_send.EmailCampaignId,
               email_campaign_send_url_conversion.EmailCampaignSendId,
               CASE WHEN sum(url_conversion.HitCount) = 0 THEN 0.0 WHEN sum(email_campaign_send_url_conversion.type * url_conversion.HitCount) > 0 THEN 100 ELSE 33.3 END AS engagement_score
        FROM email_campaign_send
        INNER JOIN email_campaign_send_url_conversion ON email_campaign_send.Id = email_campaign_send_url_conversion.EmailCampaignSendId
        INNER JOIN url_conversion ON email_campaign_send_url_conversion.UrlConversionId = url_conversion.Id
        WHERE email_campaign_send.candidateId = :candidate_id
        GROUP BY email_campaign_send_url_conversion.EmailCampaignSendId) AS engagement_score_of_all_campaigns
      NATURAL JOIN email_campaign_smart_list
      INNER JOIN smart_list ON smart_list.Id = email_campaign_smart_list.SmartListId
      INNER JOIN talent_pipeline ON talent_pipeline.id = smart_list.talentPipelineId
      WHERE talent_pipeline.id IS NOT NULL AND talent_pipeline.talent_pool_id IN :talent_pool_ids GROUP BY talent_pipeline.id
      ORDER BY average_engagement_score_of_pipeline DESC LIMIT :limit;
    """

    try:
        engagement_scores = db.session.connection().execute(text(sql_query), candidate_id=candidate_id,
                                                            limit=limit, talent_pool_ids=tuple(talent_pool_ids_of_candidate))
        return [{
                    'id': engagement_score['id'],
                    'name': engagement_score['name'],
                    'engagement_score': float(str(engagement_score['average_engagement_score_of_pipeline']))
                } for engagement_score in engagement_scores]
    except Exception as e:
        logger.exception("Couldn't compute engagement score for all pipelines of a candidate(%s) "
                         "because (%s)" % (candidate_id, e.message))
        return []


@celery_app.task(name="update_pipeline_engagement_score")
def update_pipeline_engagement_score():
    with app.app_context():
        # Updating SmartList Statistics
        logger.info("TalentPipeline Engagement Score update process has been started "
                    "at %s" % datetime.utcnow().date().isoformat())
        talent_pipelines = TalentPipeline.query.with_entities(TalentPipeline.id).all()
        talent_pipeline_ids = map(lambda talent_pipeline: talent_pipeline[0], talent_pipelines)
        talent_pipeline_cache = redis_dict(redis_store, 'pipelines_engagement_score')

        for talent_pipeline_id in talent_pipeline_ids:
            try:
                pipeline_cache_key = 'pipelines_engagement_score_%s' % talent_pipeline_id
                talent_pipeline_cache[pipeline_cache_key] = engagement_score_of_pipeline(talent_pipeline_id)
                logger.info("Engagement Score for TalentPipeline %s have been updated successfully" % talent_pipeline_id)
            except Exception as e:
                db.session.rollback()
                logger.exception("Update Engagement Score for TalentPipeline %s is not "
                                 "successful because: %s" % (talent_pipeline_id, e.message))


def get_pipeline_engagement_score(talent_pipeline_id):
    """
    This method will return talent_pipeline engagement score from Redis Cache
    :param int talent_pipeline_id: Id of TalentPipeline
    :return:
    """
    talent_pipeline_cache = redis_dict(redis_store, 'pipelines_engagement_score')
    pipeline_cache_key = 'pipelines_engagement_score_%s' % talent_pipeline_id
    if pipeline_cache_key in talent_pipeline_cache:
        logger.error("Engagement Score for TalentPipeline %s is not in cache" % talent_pipeline_id)
        return None

    return talent_pipeline_cache[pipeline_cache_key]

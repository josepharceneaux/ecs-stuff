__author__ = 'ufarooqi'
import json
import decimal
import requests
from flask import request
from datetime import datetime, timedelta, date
from candidate_pool_service.candidate_pool_app import logger, app, celery_app
from candidate_pool_service.common.redis_cache import redis_dict, redis_store
from candidate_pool_service.common.models.smartlist import SmartlistStats
from candidate_pool_service.modules.smartlists import get_candidates
from candidate_pool_service.common.error_handling import InvalidUsage
from candidate_pool_service.common.models.smartlist import Smartlist
from candidate_pool_service.common.models.talent_pools_pipelines import *
from candidate_pool_service.common.talent_config_manager import TalentConfigKeys
from candidate_pool_service.common.models.email_campaign import EmailCampaignSend
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

SCHEDULER_SERVICE_RESPONSE_CODE_TASK_ALREADY_SCHEDULED = 6057


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

    if not oauth_token:
        secret_key, oauth_token = User.generate_jw_token(user_id=talent_pipeline.user_id)
        headers = {'Authorization': oauth_token, 'X-Talent-Secret-Key-ID': secret_key,
                   'Content-Type': 'application/json'}
    else:
        headers = {'Authorization': oauth_token, 'Content-Type': 'application/json'}

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
    try:
        response = requests.get(CandidateApiUrl.CANDIDATE_SEARCH_URI, headers=headers, params=request_params)
        if response.ok:
            return response.json()
        else:
            raise Exception("Status Code: %s" % response.status_code)
    except Exception as e:
        raise InvalidUsage(error_message="Couldn't get candidates from candidates search service because: "
                                         "%s" % e.message)


def campaign_json_encoder_helper(obj):
    """JSON encoder function for SQLAlchemy special classes."""
    if isinstance(obj, date):
        return obj.isoformat()
    elif isinstance(obj, decimal.Decimal):
        return float(obj)


def get_campaigns_of_talent_pipeline(talent_pipeline):
    """
        Fetch all campaigns belonging to any smartlist of the talent-pipeline
        :param candidate_pool_service.common.models.talent_pools_pipelines.TalentPipeline talent_pipeline: Pipeline obj
        :return: A list of EmailCampaign dicts conforming to v1 of Email Campaigns API
        """

    sql_query = """
        SELECT email_campaign.*
        FROM email_campaign, email_campaign_smart_list, smart_list
        WHERE email_campaign.id=email_campaign_smart_list.emailCampaignId AND
              email_campaign_smart_list.smartListId=smart_list.id AND
              smart_list.talentPipelineId=%s"""

    email_campaigns = db.session.connection().execute(sql_query % talent_pipeline.id)
    return json.dumps([dict(email_campaign) for email_campaign in email_campaigns], default=campaign_json_encoder_helper)


@celery_app.task()
def update_smartlists_stats_task():
    """
    This method will update the statistics of all smartlists daily.
    :return: None
    """
    successful_update_smartlist_ids = []
    smartlist_ids = map(lambda smartlist: smartlist[0], Smartlist.query.with_entities(Smartlist.id).all())

    try:
        for smartlist_id in smartlist_ids:
            is_already_existing_stat_for_today = SmartlistStats.query.filter(
                    SmartlistStats.smartlist_id == smartlist_id,
                    SmartlistStats.added_datetime >= datetime.utcnow() - timedelta(hours=22),
                    SmartlistStats.added_datetime <= datetime.utcnow()).all()

            if is_already_existing_stat_for_today:
                continue
            # Return only candidate_ids
            response = get_candidates(Smartlist.query.get(smartlist_id), candidate_ids_only=True)
            total_candidates = response.get('total_found')
            smartlist_candidate_ids = [candidate.get('id') for candidate in response.get('candidates')]

            number_of_engaged_candidates = 0
            if smartlist_candidate_ids:
                number_of_engaged_candidates = db.session.query(EmailCampaignSend.candidate_id).filter(
                        EmailCampaignSend.candidate_id.in_(smartlist_candidate_ids)).count()

            percentage_candidates_engagement = int(float(number_of_engaged_candidates)/total_candidates*100) \
                if int(total_candidates) else 0
            # TODO: SMS_CAMPAIGNS are not implemented yet so we need to integrate them too here.

            smartlist_stat = SmartlistStats(smartlist_id=smartlist_id,
                                            total_number_of_candidates=total_candidates,
                                            candidates_engagement=percentage_candidates_engagement)
            db.session.add(smartlist_stat)
            db.session.commit()
            successful_update_smartlist_ids.append(str(smartlist_id))

    except Exception as e:
        db.session.rollback()
        logger.exception("An exception occured update statistics of SmartLists because: %s" % e.message)

    logger.info("Statistics for following %s SmartLists have been updated successfully: "
                "%s" % (len(successful_update_smartlist_ids), ','.join(map(str, successful_update_smartlist_ids))))


@celery_app.task()
def update_talent_pools_stats_task():
    """
    This method will update the statistics of all talent-pools daily.
    :return: None
    """
    successful_update_talent_pool_ids = []
    talent_pool_ids = map(lambda talent_pool: talent_pool[0], TalentPool.query.with_entities(TalentPool.id).all())

    try:
        for talent_pool_id in talent_pool_ids:
            is_already_existing_stat_for_today = TalentPoolStats.query.filter(
                    TalentPoolStats.talent_pool_id == talent_pool_id,
                    TalentPoolStats.added_datetime >= datetime.utcnow() - timedelta(hours=22),
                    TalentPoolStats.added_datetime <= datetime.utcnow()).all()

            if is_already_existing_stat_for_today:
                continue

            talent_pool_candidate_ids =[talent_pool_candidate.candidate_id for talent_pool_candidate in
                                        TalentPoolCandidate.query.filter_by(talent_pool_id=talent_pool_id).all()]
            total_candidates = len(talent_pool_candidate_ids)

            number_of_engaged_candidates = 0
            if talent_pool_candidate_ids:
                number_of_engaged_candidates = db.session.query(EmailCampaignSend.candidate_id).filter(
                        EmailCampaignSend.candidate_id.in_(talent_pool_candidate_ids)).count()

            percentage_candidates_engagement = int(float(number_of_engaged_candidates)/total_candidates*100) if \
                int(total_candidates) else 0
            # TODO: SMS_CAMPAIGNS are not implemented yet so we need to integrate them too here.

            talent_pool_stat = TalentPoolStats(talent_pool_id=talent_pool_id, total_number_of_candidates=total_candidates,
                                               candidates_engagement=percentage_candidates_engagement)
            db.session.add(talent_pool_stat)
            db.session.commit()
            successful_update_talent_pool_ids.append(str(talent_pool_id))

    except Exception as e:
        db.session.rollback()
        logger.exception("An exception occured update statistics of TalentPools because: %s" % e.message)

    logger.info("Statistics for following %s TalentPools have been updated successfully: "
                "%s" % (len(successful_update_talent_pool_ids), ','.join(map(str, successful_update_talent_pool_ids))))


@celery_app.task()
def update_talent_pipelines_stats_task(from_date=None, to_date=None):
    """
    This method will update the statistics of all talent-pipelines daily.
    :param from_date: DateTime Object
    :param to_date: DateTime Object
    :return: None
    """
    epoch_time_string = '12/31/1969'
    successful_update_talent_pipeline_ids = []
    talent_pipelines = TalentPipeline.query.with_entities(TalentPipeline.id).all()
    today_date = datetime.utcnow().date()
    try:
        for talent_pipeline_tuple in talent_pipelines:

            talent_pipeline_id = talent_pipeline_tuple[0]

            # TalentPipeline Object
            talent_pipeline = TalentPipeline.query.get(talent_pipeline_id)

            pipelines_growth_stats_dict = redis_dict(redis_store, 'pipelines_growth_stat_%s' % talent_pipeline_id)

            if from_date and to_date:
                last_added_stat_date = from_date
                current_date = to_date
            else:
                if len(pipelines_growth_stats_dict):
                    last_added_stat_date = max(map(lambda added_date: datetime.strptime(added_date, '%m/%d/%Y').date(),
                                                   pipelines_growth_stats_dict.keys()))
                else:
                    last_added_stat_date = talent_pipeline.added_time.date()

                current_date = today_date

            if last_added_stat_date < current_date:
                while last_added_stat_date != current_date:
                    last_added_stat_date += timedelta(days=1)
                    last_added_stat_date_string = last_added_stat_date.strftime('%m/%d/%Y')

                    if last_added_stat_date_string in pipelines_growth_stats_dict:
                        continue

                    # Get Talent Pipeline Candidates Using Search API
                    response = get_candidates_of_talent_pipeline(TalentPipeline.query.get(talent_pipeline_id),
                                                                 fields='count_only', is_celery_task=True,
                                                                 request_params={'date_from': epoch_time_string,
                                                                                 'date_to': last_added_stat_date_string})

                    pipelines_growth_stats_dict[last_added_stat_date_string] = response.get('total_found')

            logger.info("Statistics for TalentPipeline %s have been updated successfully" % talent_pipeline_id)

            successful_update_talent_pipeline_ids.append(talent_pipeline_id)

    except Exception as e:
        db.session.rollback()
        logger.exception("An exception occured update statistics of TalentPipelines because: %s" % e.message)

    logger.info("Statistics for following %s TalentPipelines have been updated successfully: "
                "%s" % (len(successful_update_talent_pipeline_ids), ','.join(map(str, successful_update_talent_pipeline_ids))))


def schedule_daily_task_unless_already_scheduled(task_name, url):
    def is_task_already_scheduled(response_dict):
        return response_dict.get('error', {}).get('code') == SCHEDULER_SERVICE_RESPONSE_CODE_TASK_ALREADY_SCHEDULED

    data = {
        "frequency": 3600 * 24,  # Daily
        "task_type": "periodic",
        "start_datetime": str(datetime.utcnow() + timedelta(seconds=10)),  # Start it 10 seconds from now
        "end_datetime": "2099-01-05T08:00:00",
        "url": url,
        "is_jwt_request": True,
        "task_name": task_name
    }

    secret_key, oauth_token = User.generate_jw_token()
    headers = {'Authorization': oauth_token, 'X-Talent-Secret-Key-ID': secret_key,
               'Content-Type': 'application/json'}

    response = requests.post(SchedulerApiUrl.TASKS, headers=headers, data=json.dumps(data))

    if is_task_already_scheduled(response.json()):
        logger.info("Task %s is already registered with scheduler service", data['task_name'])
    elif response.status_code != 201:
        raise Exception("Could not schedule task. Status Code: %s, Response: %s" % (response.status_code, response.json()))


def schedule_candidate_daily_stats_update():

    env = app.config[TalentConfigKeys.ENV_KEY]

    if env != 'jenkins':

        try:
            schedule_daily_task_unless_already_scheduled("talent_pools_daily_stats_update",
                                                         url=CandidatePoolApiUrl.TALENT_POOL_UPDATE_STATS)

            schedule_daily_task_unless_already_scheduled("talent_pipelines_daily_stats_update",
                                                         url=CandidatePoolApiUrl.TALENT_PIPELINE_UPDATE_STATS)

            schedule_daily_task_unless_already_scheduled("smartlists_daily_stats_update",
                                                         url=CandidatePoolApiUrl.SMARTLIST_UPDATE_STATS)

        except Exception as e:
            logger.exception("Couldn't register Candidate statistics update endpoint to Scheduler "
                             "Service because: %s" % e.message)

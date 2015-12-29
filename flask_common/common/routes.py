"""
This file contains Base APP URls, and Urls of REST endpoints of all services
"""

from common_config import GT_ENVIRONMENT

LOCAL_HOST = 'http://127.0.0.1'
TALENT_DOMAIN = '.gettalent.com'
QA_EXTENSION = '-webdev'


def _get_host_name(service_name, port_number):
    """
    This function gives the Base API Url depending on the environment variable.
    If api_version is provided, it also appends the version of API.

    For DEV, CIRCLE, In case of auth_service we'll get

        http://127.0.0.1:8001

    For QA:
            auth-service-webdev.gettalent.com ( for auth service)
    For PROD:
            auth-service.gettalent.com ( for auth service)

    :param service_name: Name of service
    :param port_number: Port number of service
    :type service_name: str
    :type port_number: int
    :return:
    """
    if GT_ENVIRONMENT in ['dev', 'circle']:
        return LOCAL_HOST + ':' + str(port_number) + '%s'
    elif GT_ENVIRONMENT == 'qa':
        # This looks like auth-service-webdev.gettalent.com ( for auth service)
        # TODO: Verify this URL after deployment
        return service_name + QA_EXTENSION + TALENT_DOMAIN
    elif GT_ENVIRONMENT == 'prod':
        # This looks like auth-service.gettalent.com
        # TODO: Verify this URL after deployment
        return service_name + TALENT_DOMAIN
    else:
        raise Exception("Environment variable GT_ENVIRONMENT not set correctly")


class GTApis(object):
    """
    This class contains the getTalent flask micro services' name and respective port numbers.
    """
    # Port Numbers of flask micro services
    AUTH_SERVICE_PORT = 8001
    ACTIVITY_SERVICE_PORT = 8002
    RESUME_SERVICE_PORT = 8003
    USER_SERVICE_PORT = 8004
    CANDIDATE_SERVICE_PORT = 8005
    WIDGET_SERVICE_PORT = 8006
    SOCIAL_NETWORK_SERVICE_PORT = 8007
    CANDIDATE_POOL_SERVICE_PORT = 8008
    SPREADSHEET_IMPORT_SERVICE_PORT = 8009
    DASHBOARD_SERVICE_PORT = 8010
    SCHEDULER_SERVICE_PORT = 8011
    SMS_CAMPAIGN_SERVICE_PORT = 8012
    PUSH_NOTIFICATION_SERVICE_PORT = 8013

    # Names of flask micro services
    AUTH_SERVICE_NAME = 'auth-service'
    ACTIVITY_SERVICE_NAME = 'activity-service'
    RESUME_SERVICE_NAME = 'resume-service'
    USER_SERVICE_NAME = 'user-service'
    CANDIDATE_SERVICE_NAME = 'candidate-service'
    WIDGET_SERVICE_NAME = 'widget-service'
    SOCIAL_NETWORK_SERVICE_NAME = 'social-network-service'
    CANDIDATE_POOL_SERVICE_NAME = 'candidate-pool-service'
    SPREADSHEET_IMPORT_SERVICE_NAME = 'spreadsheet-import-service'
    DASHBOARD_SERVICE_NAME = 'frontend-service'
    SMS_CAMPAIGN_SERVICE_NAME = 'sms-campaign-service'
    SCHEDULER_SERVICE_NAME = 'scheduler-service'
    PUSH_NOTIFICATION_SERVICE_NAME = 'push-notification-service'


class AuthApiUrl(object):
    """
    Rest URLs of auth_service
    """

    AUTH_HOST_NAME = _get_host_name(GTApis.AUTH_SERVICE_NAME,
                                    GTApis.AUTH_SERVICE_PORT)
    TOKEN_URL = AUTH_HOST_NAME % 'oauth2/token'


class ActivityApiUrl(object):
    """
    Rest URLs of activity_service
    """
    ACTIVITY_HOST_NAME = _get_host_name(GTApis.ACTIVITY_SERVICE_NAME,
                                        GTApis.ACTIVITY_SERVICE_PORT)
    CREATE_ACTIVITY = ACTIVITY_HOST_NAME % '/activities/'


class ResumeApiUrl(object):
    """
    Rest URLs of resume_service
    """
    RESUME_HOST_NAME = _get_host_name(GTApis.RESUME_SERVICE_NAME,
                                      GTApis.RESUME_SERVICE_PORT)


class UserApiUrl(object):
    """
    Rest URLs of user_service
    """
    User_HOST_NAME = _get_host_name(GTApis.USER_SERVICE_NAME,
                                    GTApis.USER_SERVICE_PORT)


class WidgetApiUrl(object):
    """
    Rest URLs of widget_service
    """
    WIDGET_HOST_NAME = _get_host_name(GTApis.WIDGET_SERVICE_NAME,
                                      GTApis.WIDGET_SERVICE_PORT)


class SocialNetworkApiUrl(object):
    """
    Rest URLs of social_network_service
    """
    SOCIAL_NETWORK_HOST_NAME = _get_host_name(GTApis.SOCIAL_NETWORK_SERVICE_NAME,
                                              GTApis.SOCIAL_NETWORK_SERVICE_PORT)


class CandidatePoolApiUrl(object):
    """
    Rest URLs of candidate_pool_service
    """
    CANDIDATE_POOL_HOST_NAME = _get_host_name(GTApis.CANDIDATE_POOL_SERVICE_NAME,
                                              GTApis.CANDIDATE_POOL_SERVICE_PORT)


class SpreadSheetImportApiUrl(object):
    """
    Rest URLs of spreadsheet_import_service
    """
    SPREADSHEET_IMPORT_HOST_NAME = _get_host_name(GTApis.SPREADSHEET_IMPORT_SERVICE_NAME,
                                                  GTApis.SPREADSHEET_IMPORT_SERVICE_PORT)


class SmsCampaignApi(object):
    """
    This class contains the REST endpoints of sms_campaign_service
    """
    VERSION = 'v1'
    # HOST_NAME is http://127.0.0.1:8011 for dev
    HOST_NAME = _get_host_name(GTApis.SMS_CAMPAIGN_SERVICE_NAME,
                               GTApis.SMS_CAMPAIGN_SERVICE_PORT)
    # endpoint /v1/campaigns
    # GET all campaigns of a user, POST new campaign, DELETE campaigns of a user from given ids
    CAMPAIGNS = '/%s/%s' % (VERSION, 'campaigns')

    # endpoint /v1/campaigns/:id
    # GET campaign by its id, POST: updates a campaign, DELETE a campaign from given id
    CAMPAIGN = '/%s/%s' % (VERSION, 'campaigns/<int:campaign_id>')

    # endpoint /v1/campaigns/:id/sends
    # This gives the records from "sends" for a given id of campaign
    SENDS = CAMPAIGN + '/sends'

    # endpoint /v1/campaigns/:id/send
    # To send a campaign to candidates
    SEND = CAMPAIGN + '/send'

    # /v1/campaigns/:id/schedule
    # To schedule an SMS campaign
    SCHEDULE = CAMPAIGN + '/schedule'

    """ Followings are not REST endpoints, but App endpoints """
    # endpoint /v1/receive
    # This endpoint is callback URL when candidate replies to a campaign via SMS
    RECEIVE = '/%s/%s' % (VERSION, 'receive')

    # endpoint /v1/campaigns/:id/redirect/:id?candidate_id=id
    # This endpoint is hit when candidate clicks on any URL present in SMS body text.
    APP_REDIRECTION = CAMPAIGN + '/redirect/<int:url_conversion_id>'


class SmsCampaignApiUrl(object):
    """
    This class contains the REST URLs of sms_campaign_service
    """
    """ Endpoints' complete URLs for pyTests """
    CAMPAIGNS = SmsCampaignApi.HOST_NAME % SmsCampaignApi.CAMPAIGNS
    CAMPAIGN = SmsCampaignApi.HOST_NAME % '/%s/%s' % (SmsCampaignApi.VERSION, 'campaigns/%s')
    SENDS = CAMPAIGN + '/sends'
    SEND = CAMPAIGN + '/send'
    SCHEDULE = CAMPAIGN + '/schedule'
    RECEIVE = SmsCampaignApi.HOST_NAME % SmsCampaignApi.RECEIVE
    REDIRECT = CAMPAIGN % '%s/redirect/%s'


class CandidateApiUrl(object):
    """
    Rest URLs of candidate_service
    """
    API_VERSION = 'v1'
    CANDIDATE_SERVICE_HOST_NAME = _get_host_name(GTApis.CANDIDATE_SERVICE_NAME,
                                                 GTApis.CANDIDATE_SERVICE_PORT)
    API_URL = CANDIDATE_SERVICE_HOST_NAME % '/%s%s' % (API_VERSION, '%s')
    CANDIDATE = API_URL % "/candidates/%s"
    CANDIDATES = API_URL % "/candidates"

    ADDRESS = API_URL % "/candidates/%s/addresses/%s"
    ADDRESSES = API_URL % "/candidates/%s/addresses"

    AOI = API_URL % "/candidates/%s/areas_of_interest/%s"
    AOIS = API_URL % "/candidates/%s/areas_of_interest"


    CUSTOM_FIELD = API_URL % "/candidates/%s/custom_fields/%s"
    CUSTOM_FIELDS = API_URL % "/candidates/%s/custom_fields"

    CANDIDATE_SEARCH_URI = API_URL % "/candidates/search"

    CANDIDATES_DOCUMENTS_URI = API_URL % "/candidates/documents"

    EDUCATION = API_URL % "/candidates/%s/educations/%s"
    EDUCATIONS = API_URL % "/candidates/%s/educations"

    DEGREE = API_URL % "/candidates/%s/educations/%s/degrees/%s"
    DEGREES = API_URL % "/candidates/%s/educations/%s/degrees"

    DEGREE_BULLET = API_URL % "/candidates/%s/educations/%s/degrees/%s/bullets/%s"
    DEGREE_BULLETS = API_URL % "/candidates/%s/educations/%s/degrees/%s/bullets"

    EMAIL = API_URL % "/candidates/%s/emails/%s"
    EMAILS = API_URL % "/candidates/%s/emails"

    EXPERIENCE = API_URL % "/candidates/%s/experiences/%s"
    EXPERIENCES = API_URL % "/candidates/%s/experiences"

    EXPERIENCE_BULLET = API_URL % "/candidates/%s/experiences/%s/bullets/%s"
    EXPERIENCE_BULLETS = API_URL % "/candidates/%s/experiences/%s/bullets"

    MILITARY_SERVICE = API_URL % "/candidates/%s/military_services/%s"
    MILITARY_SERVICES = API_URL % "/candidates/%s/military_services"

    PHONE = API_URL % "/candidates/%s/phones/%s"
    PHONES = API_URL % "/candidates/%s/phones"

    PREFERRED_LOCATION = API_URL % "/candidates/%s/preferred_locations/%s"
    PREFERRED_LOCATIONS = API_URL % "/candidates/%s/preferred_locations"

    SKILL = API_URL % "/candidates/%s/skills/%s"
    SKILLS = API_URL % "/candidates/%s/skills"

    SOCIAL_NETWORK = API_URL % "/candidates/%s/social_networks/%s"
    SOCIAL_NETWORKS = API_URL % "/candidates/%s/social_networks"

    WORK_PREFERENCE = API_URL % "/candidates/%s/work_preference/%s"
    CANDIDATE_EDIT = API_URL % "/candidates/%s/edits"

    SMARTLIST_CANDIDATES = API_URL % '/smartlist/get_candidates/'


class SchedulerApiUrl(object):
    """
    Rest URLs of scheduler_service
    """
    SCHEDULER_HOST_NAME = _get_host_name(GTApis.SCHEDULER_SERVICE_NAME,
                                         GTApis.SCHEDULER_SERVICE_PORT)
    CREATE_TASK = SCHEDULER_HOST_NAME % '/tasks/'
    TASKS = SCHEDULER_HOST_NAME % '/tasks/'
    TASK = SCHEDULER_HOST_NAME % '/tasks/id/%s'


class PushNotificationServiceApi(object):
    """
    REST URLs for Push Notification Service endpoints
    """
    VERSION = 'v1'
    # HOST_NAME is http://127.0.0.1:8013 for dev
    HOST_NAME = _get_host_name(GTApis.PUSH_NOTIFICATION_SERVICE_NAME,
                               GTApis.PUSH_NOTIFICATION_SERVICE_PORT)
    # endpoint /v1/campaigns
    # GET all campaigns of a user, POST new campaign, DELETE campaigns of a user from given ids
    CAMPAIGNS = '/%s/%s' % (VERSION, 'campaigns')

    # endpoint /v1/campaigns/:id
    # GET campaign by its id, POST: updates a campaign, DELETE a campaign from given id
    CAMPAIGN = '/%s/%s' % (VERSION, 'campaigns/<int:campaign_id>')

    # endpoint /v1/campaigns/:id/sends
    # This gives the records from "sends" for a given id of campaign
    SENDS = CAMPAIGN + '/sends'

    # endpoint /v1/campaigns/:id/blast
    # This gives the blast (statistics of a campaign) from "push_notification_blast" table for a given id of campaign
    BLAST = CAMPAIGN + '/blast'

    # endpoint /v1/campaigns/:id/send
    # To send a campaign to candidates
    SEND = CAMPAIGN + '/send'

    # /v1/campaigns/:id/schedule
    # To schedule an SMS campaign
    SCHEDULE = CAMPAIGN + '/schedule'

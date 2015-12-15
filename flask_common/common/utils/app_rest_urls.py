"""
This file contains Base APP URls, and Urls of REST endpoints of all services
"""

from ..common_config import GT_ENVIRONMENT
from container_config import SERVICE_TO_PORT_NUMBER

LOCAL_HOST = 'http://127.0.0.1'
TALENT_DOMAIN = '.gettalent.com'
QA_EXTENSION = '-webdev'


def _get_host_name(service_name, port_number, api_version=None):
    """
    This function gives the Base API Url depending on the environment variable.
    If api_version is provided, it also appends the version of API.

    For DEV, CIRCLE, In case of auth_service we'll get

            http://127.0.0.1:8001 in case of no api_version is provided
        and
            http://127.0.0.1:8001/v1 in case of api_version is provided.

    For QA: auth-service-webdev.gettalent.com ( for auth service)
    For PROD: auth-service.gettalent.com ( for auth service)

    :param service_name: Name of service
    :param port_number: Port number of service
    :type service_name: str
    :type port_number: str
    :return:
    """
    if GT_ENVIRONMENT in ['dev', 'circle']:
        if api_version:
            return LOCAL_HOST + ':' + port_number + api_version
        else:
            return LOCAL_HOST + ':' + port_number
    elif GT_ENVIRONMENT == 'qa':
        # This looks like auth-service-webdev.gettalent.com ( for auth service)
        # TODO: Verify this url after deployment
        return service_name + QA_EXTENSION + TALENT_DOMAIN
    elif GT_ENVIRONMENT == 'prod':
        # This looks like auth-service.gettalent.com
        # TODO: Verify this url after deployment
        return service_name + TALENT_DOMAIN
    else:
        raise Exception("Environment variable GT_ENVIRONMENT not set correctly")


class GTApis(object):
    """
    This class contains the getTalent flask micro services' name and respective port numbers.
    """

    def __init__(self):
        pass

    # Port Numbers of flask micro services
    AUTH_SERVICE_PORT = SERVICE_TO_PORT_NUMBER['auth_service']
    ACTIVITY_SERVICE_PORT = SERVICE_TO_PORT_NUMBER['activity_service']
    RESUME_SERVICE_PORT = SERVICE_TO_PORT_NUMBER['resume_service']
    USER_SERVICE_PORT = SERVICE_TO_PORT_NUMBER['user_service']
    CANDIDATE_SERVICE_PORT = SERVICE_TO_PORT_NUMBER['candidate_service']
    WIDGET_SERVICE_PORT = SERVICE_TO_PORT_NUMBER['widget_service']
    SOCIAL_NETWORK_SERVICE_PORT = SERVICE_TO_PORT_NUMBER['social_network_service']
    CANDIDATE_POOL_SERVICE_PORT = SERVICE_TO_PORT_NUMBER['candidate_pool_service']
    SPREADSHEET_IMPORT_SERVICE_PORT = SERVICE_TO_PORT_NUMBER['spreadsheet_import_service']
    SMS_CAMPAIGN_SERVICE_PORT = SERVICE_TO_PORT_NUMBER['sms_campaign_service']
    SCHEDULER_SERVICE_PORT = SERVICE_TO_PORT_NUMBER['scheduler_service']

    # Names of flask micro services
    AUTH_SERVICE_NAME = 'auth-service'
    ACTIVITY_SERVICE_NAME = 'activity-service'
    RESUME_SERVICE_NAME = 'resume-service'
    USER_SERVICE_NAME = 'user-service'
    CANDIDATE_SERVICE_NAME = 'candidate-service'
    WIDGET_SERVICE_NAME = 'widget-service'
    SOCIAL_NETWORK_SERVICE_NAME = 'social-network-service'
    CANDIDATE_POOL_SERVICE_NAME = 'candidate_pool_service'
    SPREADSHEET_IMPORT_SERVICE_NAME = 'spreadsheet_import_service'
    SMS_CAMPAIGN_SERVICE_NAME = 'sms-campaign-service'
    SCHEDULER_SERVICE_NAME = 'scheduler-service'


class AuthApiUrl(object):
    def __init__(self):
        pass

    AUTH_HOST_NAME = _get_host_name(GTApis.AUTH_SERVICE_NAME,
                                    GTApis.AUTH_SERVICE_PORT)
    OAUTH_ENDPOINT = AUTH_HOST_NAME + '/%s'
    TOKEN_URL = OAUTH_ENDPOINT % 'oauth2/token'


class ActivityApiUrl(object):
    def __init__(self):
        pass

    ACTIVITY_HOST_NAME = _get_host_name(GTApis.ACTIVITY_SERVICE_NAME,
                                        GTApis.ACTIVITY_SERVICE_PORT)
    CREATE_ACTIVITY = ACTIVITY_HOST_NAME + '/activities/'


class ResumeApiUrl(object):
    def __init__(self):
        pass

    RESUME_HOST_NAME = _get_host_name(GTApis.RESUME_SERVICE_NAME,
                                      GTApis.RESUME_SERVICE_PORT)


class UserApiUrl(object):
    def __init__(self):
        pass

    User_HOST_NAME = _get_host_name(GTApis.USER_SERVICE_NAME,
                                    GTApis.USER_SERVICE_PORT)


class WidgetApiUrl(object):
    def __init__(self):
        pass

    WIDGET_HOST_NAME = _get_host_name(GTApis.WIDGET_SERVICE_NAME,
                                      GTApis.WIDGET_SERVICE_PORT)


class SocialNetworkApiUrl(object):
    def __init__(self):
        pass

    SOCIAL_NETWORK_HOST_NAME = _get_host_name(GTApis.SOCIAL_NETWORK_SERVICE_NAME,
                                              GTApis.SOCIAL_NETWORK_SERVICE_PORT)


class CandidatePoolApiUrl(object):
    def __init__(self):
        pass

    CANDIDATE_POOL_HOST_NAME = _get_host_name(GTApis.CANDIDATE_POOL_SERVICE_NAME,
                                              GTApis.CANDIDATE_POOL_SERVICE_PORT)


class SpreadSheetImportApiUrl(object):
    def __init__(self):
        pass

    SPREADSHEET_IMPORT_HOST_NAME = _get_host_name(GTApis.SPREADSHEET_IMPORT_SERVICE_NAME,
                                                  GTApis.SPREADSHEET_IMPORT_SERVICE_PORT)


class SmsCampaignApiUrl(object):
    """
    This class contains the REST URLs of SMS Campaign API
    """

    def __init__(self):
        pass

    API_VERSION = '/v1'
    SMS_CAMPAIGN_HOST_NAME = _get_host_name(GTApis.SMS_CAMPAIGN_SERVICE_NAME,
                                            GTApis.SMS_CAMPAIGN_SERVICE_PORT,
                                            api_version=API_VERSION)
    # endpoint /campaigns
    # GET all campaigns of a user, POST new campaign, DELETE campaigns of a user from given ids
    CAMPAIGNS = SMS_CAMPAIGN_HOST_NAME + '/campaigns'
    # endpoint /campaigns/:id
    # GET campaign by its id, POST: updates a campaign, DELETE a campaign from given id
    CAMPAIGN = CAMPAIGNS + '/%s'
    # endpoint /campaigns/:id/sms_campaign_sends
    # This gives the records from "sms_campaign_sends" for a given id of campaign
    CAMPAIGN_SENDS = CAMPAIGNS + '/%s/sms_campaign_sends'
    # endpoint /campaigns/:id/send
    # To send a campaign to candidates
    CAMPAIGN_SEND_PROCESS = CAMPAIGNS + '/%s/send'
    # endpoint /url_conversion
    # This converts the given URL to shorter version using Google's Shorten URL API
    URL_CONVERSION = SMS_CAMPAIGN_HOST_NAME + '/url_conversion'
    # endpoint /receive
    # This endpoint is callback URL when candidate replies to a campaign via SMS
    SMS_RECEIVE = SMS_CAMPAIGN_HOST_NAME + '/receive'


class CandidateApiUrl(object):
    def __init__(self):
        pass

    CANDIDATE_SERVICE_HOST_NAME = _get_host_name(GTApis.CANDIDATE_SERVICE_NAME,
                                                 GTApis.CANDIDATE_SERVICE_PORT)

    CANDIDATE = CANDIDATE_SERVICE_HOST_NAME + "/v1/candidates/%s"
    CANDIDATES = CANDIDATE_SERVICE_HOST_NAME + "/v1/candidates"

    ADDRESS = CANDIDATE_SERVICE_HOST_NAME + "/v1/candidates/%s/addresses/%s"
    ADDRESSES = CANDIDATE_SERVICE_HOST_NAME + "/v1/candidates/%s/addresses"

    AOI = CANDIDATE_SERVICE_HOST_NAME + "/v1/candidates/%s/areas_of_interest/%s"
    AOIS = CANDIDATE_SERVICE_HOST_NAME + "/v1/candidates/%s/areas_of_interest"

    CUSTOM_FIELD = CANDIDATE_SERVICE_HOST_NAME + "/v1/candidates/%s/custom_fields/%s"
    CUSTOM_FIELDS = CANDIDATE_SERVICE_HOST_NAME + "/v1/candidates/%s/custom_fields"

    EDUCATION = CANDIDATE_SERVICE_HOST_NAME + "/v1/candidates/%s/educations/%s"
    EDUCATIONS = CANDIDATE_SERVICE_HOST_NAME + "/v1/candidates/%s/educations"

    DEGREE = CANDIDATE_SERVICE_HOST_NAME + "/v1/candidates/%s/educations/%s/degrees/%s"
    DEGREES = CANDIDATE_SERVICE_HOST_NAME + "/v1/candidates/%s/educations/%s/degrees"

    DEGREE_BULLET = CANDIDATE_SERVICE_HOST_NAME + "/v1/candidates/%s/educations/%s/degrees/%s/bullets/%s"
    DEGREE_BULLETS = CANDIDATE_SERVICE_HOST_NAME + "/v1/candidates/%s/educations/%s/degrees/%s/bullets"

    EMAIL = CANDIDATE_SERVICE_HOST_NAME + "/v1/candidates/%s/emails/%s"
    EMAILS = CANDIDATE_SERVICE_HOST_NAME + "/v1/candidates/%s/emails"

    EXPERIENCE = CANDIDATE_SERVICE_HOST_NAME + "/v1/candidates/%s/experiences/%s"
    EXPERIENCES = CANDIDATE_SERVICE_HOST_NAME + "/v1/candidates/%s/experiences"

    EXPERIENCE_BULLET = CANDIDATE_SERVICE_HOST_NAME + "/v1/candidates/%s/experiences/%s/bullets/%s"
    EXPERIENCE_BULLETS = CANDIDATE_SERVICE_HOST_NAME + "/v1/candidates/%s/experiences/%s/bullets"

    MILITARY_SERVICE = CANDIDATE_SERVICE_HOST_NAME + "/v1/candidates/%s/military_services/%s"
    MILITARY_SERVICES = CANDIDATE_SERVICE_HOST_NAME + "/v1/candidates/%s/military_services"

    PHONE = CANDIDATE_SERVICE_HOST_NAME + "/v1/candidates/%s/phones/%s"
    PHONES = CANDIDATE_SERVICE_HOST_NAME + "/v1/candidates/%s/phones"

    PREFERRED_LOCATION = CANDIDATE_SERVICE_HOST_NAME + "/v1/candidates/%s/preferred_locations/%s"
    PREFERRED_LOCATIONS = CANDIDATE_SERVICE_HOST_NAME + "/v1/candidates/%s/preferred_locations"

    SKILL = CANDIDATE_SERVICE_HOST_NAME + "/v1/candidates/%s/skills/%s"
    SKILLS = CANDIDATE_SERVICE_HOST_NAME + "/v1/candidates/%s/skills"

    SOCIAL_NETWORK = CANDIDATE_SERVICE_HOST_NAME + "/v1/candidates/%s/social_networks/%s"
    SOCIAL_NETWORKS = CANDIDATE_SERVICE_HOST_NAME + "/v1/candidates/%s/social_networks"

    WORK_PREFERENCE = CANDIDATE_SERVICE_HOST_NAME + "/v1/candidates/%s/work_preference/%s"
    SMARTLIST_CANDIDATES = CANDIDATE_SERVICE_HOST_NAME + '/v1/smartlist/get_candidates/'


class SchedulerApiUrl(object):
    def __init__(self):
        pass

    SCHEDULER_HOST_NAME = _get_host_name(GTApis.SCHEDULER_SERVICE_NAME,
                                         GTApis.SCHEDULER_SERVICE_PORT)

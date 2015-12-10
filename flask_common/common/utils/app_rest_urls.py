"""
This file contains Base APP URls, and Urls of REST endpoints of all services
"""

from ..common_config import GT_ENVIRONMENT

LOCAL_HOST = 'http://127.0.0.1'
TALENT_DOMAIN = '.gettalent.com'
QA_EXTENSION = '-webdev'


def _base_api_url(service_name, port_number):
    """
    This function gives the Base API Url depending on the environment variable
    :param service_name: Name of service
    :param port_number: Port number of service
    :type service_name: str
    :type port_number: str
    :return:
    """
    if GT_ENVIRONMENT in ['dev', 'circle']:
        return LOCAL_HOST + ':' + port_number
    elif GT_ENVIRONMENT == 'qa':
        return service_name + QA_EXTENSION + TALENT_DOMAIN
    elif GT_ENVIRONMENT == 'prod':
        return service_name + TALENT_DOMAIN
    else:
        raise Exception("Environment variable GT_ENVIRONMENT not set correctly")


class GTApps:
    def __init__(self):
        pass
    
    # Port Numbers of micro services
    AUTH_SERVICE_PORT = '8001'
    ACTIVITY_SERVICE_PORT = '8002'
    RESUME_SERVICE_PORT = '8003'
    USER_SERVICE_PORT = '8004'
    CANDIDATE_SERVICE_PORT = '8005'
    WIDGET_SERVICE_PORT = '8006'
    SOCIAL_NETWORK_SERVICE_PORT = '8007'
    SMS_CAMPAIGN_SERVICE_PORT = '8008'
    SCHEDULER_CAMPAIGN_SERVICE_PORT = '8009'
    
    # Names of micro services
    AUTH_SERVICE_NAME = 'auth-service'
    ACTIVITY_SERVICE_NAME = 'activity-service'
    RESUME_SERVICE_NAME = 'resume-service'
    USER_SERVICE_NAME = 'user-service'
    CANDIDATE_SERVICE_NAME = 'candidate-service'
    WIDGET_SERVICE_NAME = 'widget-service'
    SOCIAL_NETWORK_SERVICE_NAME = 'social-network-service'
    SMS_CAMPAIGN_SERVICE_NAME = 'sms-campaign-service'
    SCHEDULER_CAMPAIGN_SERVICE_NAME = 'scheduler-service'


class AuthApiUrl:
    def __init__(self):
        pass

    AUTH_API_URL = _base_api_url(GTApps.AUTH_SERVICE_NAME,
                                 GTApps.AUTH_SERVICE_PORT)


class ActivityApiUrl:
    def __init__(self):
        pass

    ACTIVITY_API_URL = _base_api_url(GTApps.ACTIVITY_SERVICE_NAME,
                                     GTApps.ACTIVITY_SERVICE_PORT)
    CREATE_ACTIVITY = ACTIVITY_API_URL + '/activities/'


class ResumeApiUrl:
    def __init__(self):
        pass

    RESUME_API_URL = _base_api_url(GTApps.RESUME_SERVICE_NAME,
                                   GTApps.RESUME_SERVICE_PORT)


class UserApiUrl:
    def __init__(self):
        pass

    User_API_URL = _base_api_url(GTApps.USER_SERVICE_NAME,
                                 GTApps.USER_SERVICE_PORT)


class WidgetApiUrl:
    def __init__(self):
        pass

    WIDGET_API_URL = _base_api_url(GTApps.WIDGET_SERVICE_NAME,
                                   GTApps.WIDGET_SERVICE_PORT)


class SocialNetworkApiUrl:
    def __init__(self):
        pass

    SOCIAL_NETWORK_API_URL = _base_api_url(GTApps.SOCIAL_NETWORK_SERVICE_NAME,
                                           GTApps.SCHEDULER_CAMPAIGN_SERVICE_PORT)


class SmsCampaignApiUrl:
    def __init__(self):
        pass

    API_URL = _base_api_url(GTApps.SMS_CAMPAIGN_SERVICE_NAME,
                            GTApps.SMS_CAMPAIGN_SERVICE_PORT)
    # endpoint /campaigns/
    CAMPAIGNS = API_URL + '/campaigns/'
    # endpoint /campaigns/:id
    CAMPAIGN = CAMPAIGNS + '%s'
    # endpoint /campaigns/:id/sends
    CAMPAIGN_SENDS = CAMPAIGNS + '%s/sms_campaign_sends'
    # endpoint /campaigns/:id/send
    CAMPAIGN_SEND_PROCESS = CAMPAIGNS + '%s/send'
    # endpoint /url_conversion
    URL_CONVERSION = API_URL + '/url_conversion'
    # endpoint /sms_receive
    SMS_RECEIVE = API_URL + '/sms_receive'


class CandidateApiUrl:
    def __init__(self):
        pass

    API_URL = _base_api_url(GTApps.CANDIDATE_SERVICE_NAME,
                            GTApps.CANDIDATE_SERVICE_PORT)

    CANDIDATE = API_URL + "/v1/candidates/%s"
    CANDIDATES = API_URL + "/v1/candidates"

    ADDRESS = API_URL + "/v1/candidates/%s/addresses/%s"
    ADDRESSES = API_URL + "/v1/candidates/%s/addresses"

    AOI = API_URL + "/v1/candidates/%s/areas_of_interest/%s"
    AOIS = API_URL + "/v1/candidates/%s/areas_of_interest"

    CUSTOM_FIELD = API_URL + "/v1/candidates/%s/custom_fields/%s"
    CUSTOM_FIELDS = API_URL + "/v1/candidates/%s/custom_fields"

    EDUCATION = API_URL + "/v1/candidates/%s/educations/%s"
    EDUCATIONS = API_URL + "/v1/candidates/%s/educations"

    DEGREE = API_URL + "/v1/candidates/%s/educations/%s/degrees/%s"
    DEGREES = API_URL + "/v1/candidates/%s/educations/%s/degrees"

    DEGREE_BULLET = API_URL + "/v1/candidates/%s/educations/%s/degrees/%s/bullets/%s"
    DEGREE_BULLETS = API_URL + "/v1/candidates/%s/educations/%s/degrees/%s/bullets"

    EMAIL = API_URL + "/v1/candidates/%s/emails/%s"
    EMAILS = API_URL + "/v1/candidates/%s/emails"

    EXPERIENCE = API_URL + "/v1/candidates/%s/experiences/%s"
    EXPERIENCES = API_URL + "/v1/candidates/%s/experiences"

    EXPERIENCE_BULLET = API_URL + "/v1/candidates/%s/experiences/%s/bullets/%s"
    EXPERIENCE_BULLETS = API_URL + "/v1/candidates/%s/experiences/%s/bullets"

    MILITARY_SERVICE = API_URL + "/v1/candidates/%s/military_services/%s"
    MILITARY_SERVICES = API_URL + "/v1/candidates/%s/military_services"

    PHONE = API_URL + "/v1/candidates/%s/phones/%s"
    PHONES = API_URL + "/v1/candidates/%s/phones"

    PREFERRED_LOCATION = API_URL + "/v1/candidates/%s/preferred_locations/%s"
    PREFERRED_LOCATIONS = API_URL + "/v1/candidates/%s/preferred_locations"

    SKILL = API_URL + "/v1/candidates/%s/skills/%s"
    SKILLS = API_URL + "/v1/candidates/%s/skills"

    SOCIAL_NETWORK = API_URL + "/v1/candidates/%s/social_networks/%s"
    SOCIAL_NETWORKS = API_URL + "/v1/candidates/%s/social_networks"

    WORK_PREFERENCE = API_URL + "/v1/candidates/%s/work_preference/%s"
    SMARTLIST_CANDIDATES = API_URL + '/v1/smartlist/get_candidates/'


class SchedulerApiUrl:
    def __init__(self):
        pass

    SCHEDULER_API_URL = _base_api_url(GTApps.SCHEDULER_CAMPAIGN_SERVICE_NAME,
                                      GTApps.SMS_CAMPAIGN_SERVICE_PORT)

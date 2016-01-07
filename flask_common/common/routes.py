"""
This file contains Base APP URls, and Urls of REST endpoints of all services
"""
import os
from talent_config_manager import TalentConfigKeys

LOCAL_HOST = 'http://127.0.0.1'
TALENT_DOMAIN = '.gettalent.com'
HEALTH_CHECK = '/healthcheck'


def _get_host_name(service_name, port_number):
    """
    This function gives the Base API Url depending on the environment variable.
    If api_version is provided, it also appends the version of API.

    For DEV, CIRCLE, In case of auth_service we'll get

        http://127.0.0.1:8001%s

    For QA:
            auth-service-staging.gettalent.com (for auth service)
    For PROD:
            auth-service.gettalent.com (for auth service)

    :param service_name: Name of service
    :param port_number: Port number of service
    :type service_name: str
    :type port_number: int
    :return:
    """
    env = os.getenv(TalentConfigKeys.ENV_KEY) or 'dev'
    if env in ['dev', 'circle']:
        return LOCAL_HOST + ':' + str(port_number) + '%s'
    elif env == 'qa':
        # This looks like auth-service-webdev.gettalent.com (for auth service)
        # TODO: Verify this URL after deployment
        return service_name + '-staging' + TALENT_DOMAIN
    elif env == 'prod':
        # This looks like auth-service.gettalent.com (for auth service)
        # TODO: Verify this URL after deployment
        return service_name + TALENT_DOMAIN
    else:
        raise Exception("Environment variable GT_ENVIRONMENT not set correctly")


def _get_api_relative_url(api_version):
    """
    Given version of API, this returns e.g. /v1/%s
    :param api_version:
    :return:
    """
    return '/%s/%s' % (api_version, '%s')


def _get_url_prefix(api_version):
    """
    For given API version this gives url_prefix to be used for API registration
    e.g if api_version is v1, it will return /v1/
    :param api_version: version of API
    """
    return '/' + api_version + '/'


def _get_health_check_url(host_name):
    """
    This returns the healthcheck url appended with host name. e.g.http://127.0.0.1:8001/healthcheck
    :param host_name: name of host. e.g.http://127.0.0.1:8001
    """
    return host_name % HEALTH_CHECK


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


class AuthApi(object):
    """
    Rest endpoints of auth_service
    """
    VERSION = 'v1'
    API_URL = _get_api_relative_url(VERSION)
    TOKEN_CREATE = API_URL % 'oauth2/token'
    TOKEN_REVOKE = API_URL % 'oauth2/revoke'
    AUTHORIZE = API_URL % 'oauth2/authorize'


class AuthApiUrl(object):
    """
    Rest URLs of auth_service
    """
    HOST_NAME = _get_host_name(GTApis.AUTH_SERVICE_NAME,
                                            GTApis.AUTH_SERVICE_PORT)
    HEALTH_CHECK = _get_health_check_url(HOST_NAME)
    TOKEN_CREATE = HOST_NAME % AuthApi.TOKEN_CREATE
    TOKEN_REVOKE = HOST_NAME % AuthApi.TOKEN_REVOKE
    AUTHORIZE = HOST_NAME % AuthApi.AUTHORIZE


class ActivityApi(object):
    """
    Rest endpoints of activity_service
    """
    VERSION = 'v1'
    API_URL = _get_api_relative_url(VERSION)
    # /v1/activities/
    ACTIVITIES = API_URL % 'activities/'
    # /v1/activities/<page>
    ACTIVITIES_PAGE = ACTIVITIES + '<page>'


class ActivityApiUrl(object):
    """
    Rest URLs of activity_service
    """
    HOST_NAME = _get_host_name(GTApis.ACTIVITY_SERVICE_NAME,
                               GTApis.ACTIVITY_SERVICE_PORT)
    HEALTH_CHECK = _get_health_check_url(HOST_NAME)
    ACTIVITIES = HOST_NAME % ActivityApi.ACTIVITIES
    ACTIVITIES_PAGE = ACTIVITIES + '%s'


class ResumeApi(object):
    """
    Rest endpoints of resume_service
    """
    VERSION = 'v1'
    URL_PREFIX = _get_url_prefix(VERSION)
    API_URL = _get_api_relative_url(VERSION)
    PARSE = 'parse_resume'


class ResumeApiUrl(object):
    """
    Rest URLs of resume_service
    """
    HOST_NAME = _get_host_name(GTApis.RESUME_SERVICE_NAME,
                               GTApis.RESUME_SERVICE_PORT)
    HEALTH_CHECK = _get_health_check_url(HOST_NAME)
    API_URL = HOST_NAME % ResumeApi.API_URL
    PARSE = API_URL % ResumeApi.PARSE


class UserServiceApi:
    """
    Rest endpoints of user_service
    """

    def __init__(self):
        pass

    VERSION = 'v1'
    URL_PREFIX = _get_url_prefix(VERSION)
    USERS = 'users'
    DOMAINS = 'domains'
    _GROUPS = 'groups'
    _GROUP = _GROUPS + '/<int:group_id>/'
    USER = USERS + "/<int:id>"
    DOMAIN = DOMAINS + "/<int:id>"
    USER_ROLES = USERS + "/<int:user_id>/roles"
    DOMAIN_ROLES = 'domain/<int:domain_id>/roles'
    DOMAIN_GROUPS = "domain/<int:domain_id>/" + _GROUPS
    DOMAIN_GROUPS_UPDATE = "domain/" + _GROUPS + '/<int:group_id>'
    USER_GROUPS = _GROUP + USERS
    UPDATE_PASSWORD = USERS + '/update_password'
    FORGOT_PASSWORD = USERS + '/forgot_password'
    RESET_PASSWORD = USERS + '/reset_password/<token>'


class UserServiceApiUrl:
    """
    Rest URLs of user_service
    """

    def __init__(self):
        pass

    API_VERSION = 'v1'
    HOST_NAME = _get_host_name(GTApis.USER_SERVICE_NAME,
                                            GTApis.USER_SERVICE_PORT)
    HEALTH_CHECK = _get_health_check_url(HOST_NAME)
    API_URL = HOST_NAME % '/%s/%s' % (API_VERSION, '%s')
    USERS = API_URL % UserServiceApi.USERS
    USER = USERS + '/%s'
    DOMAINS = API_URL % UserServiceApi.DOMAINS
    DOMAIN = DOMAINS + '/%s'
    USER_ROLES_API = API_URL % 'users/%s/roles'
    DOMAIN_ROLES_API = API_URL % 'domain/%s/roles'
    DOMAIN_GROUPS_API = API_URL % 'domain/%s/groups'
    DOMAIN_GROUPS_UPDATE_API = API_URL % 'domain/groups/%s'
    USER_GROUPS_API = API_URL % 'groups/%s/users'
    UPDATE_PASSWORD_API = API_URL % UserServiceApi.UPDATE_PASSWORD
    FORGOT_PASSWORD_API = API_URL % UserServiceApi.FORGOT_PASSWORD
    RESET_PASSWORD_API = API_URL % UserServiceApi.RESET_PASSWORD


class WidgetApi(object):
    """
    Rest endpoints of widget_service
    """
    VERSION = 'v1'
    # This is /v1/
    URL_PREFIX = _get_url_prefix(VERSION)
    DOMAINS = 'domains'
    _ENCRYPTED_DOMAIN_ID = '/<path:encrypted_domain_id>'
    DOMAIN_WIDGETS = DOMAINS + _ENCRYPTED_DOMAIN_ID + '/widgets/<path:encrypted_widget_id>'
    DOMAIN_INTERESTS = DOMAINS + _ENCRYPTED_DOMAIN_ID + '/interests'
    DOMAIN_MAJORS = DOMAINS + _ENCRYPTED_DOMAIN_ID + '/majors'
    UNIVERSITIES = 'universities'


class WidgetApiUrl(object):
    """
    Rest URLs of widget_service
    """
    HOST_NAME = _get_host_name(GTApis.WIDGET_SERVICE_NAME,
                                      GTApis.WIDGET_SERVICE_PORT)
    HEALTH_CHECK = _get_health_check_url(HOST_NAME)
    API_URL = HOST_NAME % '/%s/%s' % (WidgetApi.VERSION, '%s')
    DOMAIN_WIDGETS = API_URL % (WidgetApi.DOMAINS + '/%s/widgets/%s')
    DOMAIN_INTERESTS = API_URL % (WidgetApi.DOMAINS + '/%s/interests')
    UNIVERSITIES = API_URL % WidgetApi.UNIVERSITIES
    DOMAIN_MAJORS = API_URL % (WidgetApi.DOMAINS + '/%s/majors')
    DOMAINS = API_URL % UserServiceApi.DOMAINS


class SocialNetworkApiUrl(object):
    """
    Rest URLs of social_network_service
    """
    HOST_NAME = _get_host_name(GTApis.SOCIAL_NETWORK_SERVICE_NAME,
                                              GTApis.SOCIAL_NETWORK_SERVICE_PORT)
    HEALTH_CHECK = _get_health_check_url(HOST_NAME)


class CandidatePoolApiUrl(object):
    """
    Rest URLs of candidate_pool_service
    """
    API_VERSION = 'v1'
    HOST_NAME = _get_host_name(GTApis.CANDIDATE_POOL_SERVICE_NAME,
                               GTApis.CANDIDATE_POOL_SERVICE_PORT)
    HEALTH_CHECK = _get_health_check_url(HOST_NAME)
    API_URL = HOST_NAME % '/%s/%s' % (API_VERSION, '%s')
    TALENT_POOL_STATS = API_URL % "talent-pools/stats"
    TALENT_POOL_GET_STATS = API_URL % "talent-pool/%s/stats"
    TALENT_PIPELINE_STATS = API_URL % "talent-pipelines/stats"
    TALENT_PIPELINE_GET_STATS = API_URL % "talent-pipeline/%s/stats"
    SMARTLIST_CANDIDATES = API_URL % 'smartlists/%s/candidates'
    SMARTLISTS = API_URL % 'smartlists'
    SMARTLIST_STATS = HOST_NAME % "smartlists/stats"
    SMARTLIST_GET_STATS = HOST_NAME % "smartlists/%s/stats"


class SpreadsheetImportApi(object):
    """
    Rest URLs of spreadsheet_import_service
    """
    VERSION = 'v1'
    # This is /v1/
    URL_PREFIX = _get_url_prefix(VERSION)
    _PARSE_SPREADSHEET = 'parse_spreadsheet'
    CONVERT_TO_TABLE = _PARSE_SPREADSHEET + '/convert_to_table/'
    IMPORT_CANDIDATES = _PARSE_SPREADSHEET + '/import_candidates'


class SpreadsheetImportApiUrl(object):
    """
    Rest URLs of spreadsheet_import_service
    """
    HOST_NAME = _get_host_name(GTApis.SPREADSHEET_IMPORT_SERVICE_NAME,
                                                          GTApis.SPREADSHEET_IMPORT_SERVICE_PORT)
    HEALTH_CHECK = _get_health_check_url(HOST_NAME)
    API_URL = HOST_NAME % '/%s/%s' % (SpreadsheetImportApi.VERSION, '%s')
    CONVERT_TO_TABLE = API_URL % "convert_to_table"
    IMPORT_CANDIDATES = API_URL % 'import_candidates'


class CandidateApiUrl(object):
    """
    Rest URLs of candidate_service
    """
    API_VERSION = 'v1'
    HOST_NAME = _get_host_name(GTApis.CANDIDATE_SERVICE_NAME,
                                                 GTApis.CANDIDATE_SERVICE_PORT)
    API_URL = HOST_NAME % '/%s%s' % (API_VERSION, '%s')
    HEALTH_CHECK = _get_health_check_url(HOST_NAME)
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


class SchedulerApiUrl(object):
    """
    Rest URLs of scheduler_service
    """
    SCHEDULER_SERVICE_HOST_NAME = _get_host_name(GTApis.SCHEDULER_SERVICE_NAME,
                                                 GTApis.SCHEDULER_SERVICE_PORT)
    TASKS = SCHEDULER_SERVICE_HOST_NAME % '/tasks/'
    TASK = SCHEDULER_SERVICE_HOST_NAME % '/tasks/id/%s'


class SchedulerApi(object):
    """
    Rest Emdpoints for scheduler_service
    """
    VERSION = 'v1'
    # HOST_NAME is http://127.0.0.1:8011 for dev
    SCHEDULER_SERVICE_HOST_NAME = _get_host_name(GTApis.SCHEDULER_SERVICE_NAME,
                                                 GTApis.SCHEDULER_SERVICE_PORT)
    API_URL = '/%s/%s' % (VERSION, '%s')
    HEALTH_CHECK = _get_health_check_url(SCHEDULER_SERVICE_HOST_NAME)
    TASKS = API_URL % '/tasks/'
    TASK = API_URL % '/tasks/id/<string:_id>'

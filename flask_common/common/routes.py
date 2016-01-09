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


def _get_api_relative_version(api_version):
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
    SCHEDULER_SERVICE_NAME = 'scheduler-service'
    SMS_CAMPAIGN_SERVICE_NAME = 'sms-campaign-service'


class AuthApi(object):
    """
    API relative URLs for auth_service. e.g. /v1/oauth2/token
    """
    VERSION = 'v1'
    RELATIVE_VERSION = _get_api_relative_version(VERSION)
    TOKEN_CREATE = RELATIVE_VERSION % 'oauth2/token'
    TOKEN_REVOKE = RELATIVE_VERSION % 'oauth2/revoke'
    AUTHORIZE = RELATIVE_VERSION % 'oauth2/authorize'


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
    API relative URLs for activity_service. e.g /v1/activities/
    """
    VERSION = 'v1'
    RELATIVE_VERSION = _get_api_relative_version(VERSION)
    # /v1/activities/
    ACTIVITIES = RELATIVE_VERSION % 'activities/'
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
    API relative URLs for resume_service. e.g. /v1/parse_resume
    """
    VERSION = 'v1'
    URL_PREFIX = _get_url_prefix(VERSION)
    RELATIVE_VERSION = _get_api_relative_version(VERSION)
    PARSE = 'parse_resume'


class ResumeApiUrl(object):
    """
    Rest URLs of resume_service
    """
    HOST_NAME = _get_host_name(GTApis.RESUME_SERVICE_NAME,
                               GTApis.RESUME_SERVICE_PORT)
    HEALTH_CHECK = _get_health_check_url(HOST_NAME)
    API_URL = HOST_NAME % ResumeApi.RELATIVE_VERSION
    PARSE = API_URL % ResumeApi.PARSE


class UserServiceApi(object):
    """
    API relative URLs for user_service. e.g. /v1/users
    """
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


class UserServiceApiUrl(object):
    """
    Rest URLs of user_service
    """
    HOST_NAME = _get_host_name(GTApis.USER_SERVICE_NAME,
                               GTApis.USER_SERVICE_PORT)
    HEALTH_CHECK = _get_health_check_url(HOST_NAME)
    API_URL = HOST_NAME % _get_api_relative_version(UserServiceApi.VERSION)
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
    RESET_PASSWORD_API = USERS + '/reset_password/%s'


class WidgetApi(object):
    """
    API relative URLs for widget_service. e.g. /v1/universities
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
    API_URL = HOST_NAME % _get_api_relative_version(WidgetApi.VERSION)
    DOMAIN_WIDGETS = API_URL % (WidgetApi.DOMAINS + '/%s/widgets/%s')
    DOMAIN_INTERESTS = API_URL % (WidgetApi.DOMAINS + '/%s/interests')
    DOMAIN_MAJORS = API_URL % (WidgetApi.DOMAINS + '/%s/majors')
    DOMAINS = API_URL % UserServiceApi.DOMAINS
    UNIVERSITIES = API_URL % WidgetApi.UNIVERSITIES


class SocialNetworkApiUrl(object):
    """
    API relative URLs for social_network_service
    """
    HOST_NAME = _get_host_name(GTApis.SOCIAL_NETWORK_SERVICE_NAME,
                               GTApis.SOCIAL_NETWORK_SERVICE_PORT)
    HEALTH_CHECK = _get_health_check_url(HOST_NAME)


class CandidatePoolApi(object):
    """
    API relative URLs for candidate_pool_service. e.g. /v1/smartlists
    """
    VERSION = 'v1'
    # /v1/
    URL_PREFIX = _get_url_prefix(VERSION)
    _INT_ID = '/<int:id>'
    _TALENT_POOL = 'talent-pool'
    _TALENT_PIPELINE = 'talent-pipeline'
    _STATS = '/stats'
    # Talent Pools
    TALENT_POOLS = 'talent-pools'
    TALENT_POOL = TALENT_POOLS + _INT_ID
    TALENT_POOL_CANDIDATES = TALENT_POOL + '/candidates'
    TALENT_POOL_GROUPS = 'groups/<int:group_id>/talent_pools'
    TALENT_POOL_STATS = TALENT_POOLS + _STATS
    TALENT_POOL_GET_STATS = _TALENT_POOL + '/<int:talent_pool_id>' + _STATS
    # Talent Pipelines
    TALENT_PIPELINES = 'talent-pipelines'
    TALENT_PIPELINE = TALENT_PIPELINES + _INT_ID
    TALENT_PIPELINE_SMARTLISTS = _TALENT_PIPELINE + _INT_ID + '/smart_lists'
    TALENT_PIPELINE_CANDIDATES = _TALENT_PIPELINE + _INT_ID + '/candidates'
    TALENT_PIPELINE_STATS = TALENT_PIPELINES + _STATS
    TALENT_PIPELINE_GET_STATS = _TALENT_PIPELINE + '/<int:talent_pipeline_id>' + _STATS
    # Smartlists
    SMARTLISTS = 'smartlists'
    SMARTLIST = SMARTLISTS + _INT_ID
    SMARTLIST_CANDIDATES = SMARTLISTS + '/<int:smartlist_id>/candidates'
    SMARTLIST_STATS = SMARTLISTS + _STATS
    SMARTLIST_GET_STATS = SMARTLISTS + '/<int:smartlist_id>' + _STATS


class CandidatePoolApiUrl(object):
    """
    Rest URLs of candidate_pool_service
    """
    HOST_NAME = _get_host_name(GTApis.CANDIDATE_POOL_SERVICE_NAME,
                               GTApis.CANDIDATE_POOL_SERVICE_PORT)
    HEALTH_CHECK = _get_health_check_url(HOST_NAME)
    API_URL = HOST_NAME % _get_api_relative_version(CandidatePoolApi.VERSION)
    # Talent Pool
    TALENT_POOLS = API_URL % CandidatePoolApi.TALENT_POOLS
    TALENT_POOL = TALENT_POOLS + '/%s'
    TALENT_POOL_STATS = API_URL % CandidatePoolApi.TALENT_POOL_STATS
    TALENT_POOL_GET_STATS = API_URL % "talent-pool/%s/stats"
    TALENT_POOL_CANDIDATE = API_URL % (CandidatePoolApi.TALENT_POOLS + '/%s/candidates')
    TALENT_POOL_GROUP = API_URL % 'groups/%s/talent_pools'
    # Talent Pipeline
    TALENT_PIPELINES = API_URL % CandidatePoolApi.TALENT_PIPELINES
    TALENT_PIPELINE = TALENT_PIPELINES + '/%s'
    TALENT_PIPELINE_STATS = API_URL % CandidatePoolApi.TALENT_PIPELINE_STATS
    TALENT_PIPELINE_CANDIDATE = API_URL % 'talent-pipeline/%s/candidates'
    TALENT_PIPELINE_SMARTLISTS = API_URL % 'talent-pipeline/%s/smart_lists'
    TALENT_PIPELINE_GET_STATS = API_URL % "talent-pipeline/%s/stats"
    # Smartlists
    SMARTLISTS = API_URL % CandidatePoolApi.SMARTLISTS
    SMARTLIST_STATS = API_URL % CandidatePoolApi.SMARTLIST_STATS
    SMARTLIST_GET_STATS = SMARTLISTS + "/%s/stats"
    SMARTLIST_CANDIDATES = SMARTLISTS + '/%s/candidates'


class SpreadsheetImportApi(object):
    """
    API relative URLs for spreadsheet_import_service. e.g. /v1/parse_spreadsheet/convert_to_table
    """
    VERSION = 'v1'
    # This is /v1/
    URL_PREFIX = _get_url_prefix(VERSION)
    _PARSE_SPREADSHEET = 'parse_spreadsheet'
    CONVERT_TO_TABLE = _PARSE_SPREADSHEET + '/convert_to_table'
    IMPORT_CANDIDATES = _PARSE_SPREADSHEET + '/import_candidates'


class SpreadsheetImportApiUrl(object):
    """
    Rest URLs of spreadsheet_import_service
    """
    HOST_NAME = _get_host_name(GTApis.SPREADSHEET_IMPORT_SERVICE_NAME,
                               GTApis.SPREADSHEET_IMPORT_SERVICE_PORT)
    HEALTH_CHECK = _get_health_check_url(HOST_NAME)
    API_URL = HOST_NAME % _get_api_relative_version(SpreadsheetImportApi.VERSION)
    CONVERT_TO_TABLE = API_URL % SpreadsheetImportApi.CONVERT_TO_TABLE
    IMPORT_CANDIDATES = API_URL % SpreadsheetImportApi.IMPORT_CANDIDATES


class CandidateApi(object):
    """
    API relative URLs for candidate_service. e,g /v1/candidates
    """
    VERSION = 'v1'
    _INT_ID = "/<int:id>"
    HOST_NAME = _get_host_name(GTApis.CANDIDATE_SERVICE_NAME,
                               GTApis.CANDIDATE_SERVICE_PORT)
    RELATIVE_VERSION = '/%s/%s' % (VERSION, '%s')
    HEALTH_CHECK = _get_health_check_url(HOST_NAME)

    CANDIDATES = RELATIVE_VERSION % "candidates"
    _CANDIDATE_ID = CANDIDATES + "/<int:candidate_id>"
    CANDIDATE_ID = RELATIVE_VERSION % "candidates/<int:id>"
    CANDIDATE_EMAIL = RELATIVE_VERSION % "candidates/<email>"

    ADDRESSES = _CANDIDATE_ID + "/addresses"
    ADDRESS = ADDRESSES + _INT_ID

    AOIS = _CANDIDATE_ID + "/areas_of_interest"
    AOI = AOIS + _INT_ID

    CUSTOM_FIELDS = _CANDIDATE_ID + "/custom_fields"
    CUSTOM_FIELD = CUSTOM_FIELDS + _INT_ID

    EDUCATIONS = _CANDIDATE_ID + "/educations"
    EDUCATION = EDUCATIONS + _INT_ID

    DEGREES = EDUCATIONS + '/<int:education_id>/degrees'
    DEGREE = DEGREES + _INT_ID

    DEGREE_BULLETS = DEGREES + "/<int:degree_id>/bullets"
    DEGREE_BULLET = DEGREE_BULLETS + _INT_ID

    EXPERIENCES = _CANDIDATE_ID + "/experiences"
    EXPERIENCE = EXPERIENCES + _INT_ID

    EXPERIENCE_BULLETS = EXPERIENCES + "/<int:experience_id>/bullets"
    EXPERIENCE_BULLET = EXPERIENCE_BULLETS + _INT_ID

    EMAILS = _CANDIDATE_ID + "/emails"
    EMAIL = EMAILS + _INT_ID

    MILITARY_SERVICES = _CANDIDATE_ID + "/military_services"
    MILITARY_SERVICE = MILITARY_SERVICES + _INT_ID

    PHONES = _CANDIDATE_ID + "/phones"
    PHONE = PHONES + _INT_ID

    PREFERRED_LOCATIONS = _CANDIDATE_ID + "/preferred_locations"
    PREFERRED_LOCATION = PREFERRED_LOCATIONS + _INT_ID

    SKILLS = _CANDIDATE_ID + "/skills"
    SKILL = SKILLS + _INT_ID

    SOCIAL_NETWORKS = _CANDIDATE_ID + "/social_networks"
    SOCIAL_NETWORK = SOCIAL_NETWORKS + _INT_ID

    WORK_PREFERENCE = _CANDIDATE_ID + "/work_preference" + _INT_ID
    CANDIDATE_EDIT = CANDIDATE_ID + "/edits"

    CANDIDATE_SEARCH = CANDIDATES + "/search"
    CANDIDATES_DOCUMENTS = CANDIDATES + "/documents"
    OPENWEB = CANDIDATES + '/openweb'


class CandidateApiUrl(object):
    """
    Rest URLs of candidate_service
    """
    HOST_NAME = _get_host_name(GTApis.CANDIDATE_SERVICE_NAME,
                               GTApis.CANDIDATE_SERVICE_PORT)
    HEALTH_CHECK = _get_health_check_url(HOST_NAME)
    CANDIDATES = HOST_NAME % CandidateApi.CANDIDATES
    CANDIDATE = CANDIDATES + "/%s"

    ADDRESSES = CANDIDATE + "/addresses"
    ADDRESS = ADDRESSES + "/%s"

    AOIS = CANDIDATE + "/areas_of_interest"
    AOI = AOIS + "/%s"

    CUSTOM_FIELDS = CANDIDATE + "/custom_fields"
    CUSTOM_FIELD = CUSTOM_FIELDS + "/%s"

    CANDIDATE_SEARCH_URI = CANDIDATES + "/search"

    CANDIDATES_DOCUMENTS_URI = CANDIDATES + "/documents"

    EDUCATIONS = CANDIDATE + "/educations"
    EDUCATION = EDUCATIONS + "/%s"

    DEGREES = EDUCATION + "/degrees"
    DEGREE = DEGREES + "/%s"

    DEGREE_BULLETS = DEGREE + "/bullets"
    DEGREE_BULLET = DEGREE_BULLETS + "/%s"

    EMAILS = CANDIDATE + "/emails"
    EMAIL = EMAILS + "/%s"

    EXPERIENCES = CANDIDATE + "/experiences"
    EXPERIENCE = EXPERIENCES + "/%s"

    EXPERIENCE_BULLETS = EXPERIENCE + "/bullets"
    EXPERIENCE_BULLET = EXPERIENCE_BULLETS + "/%s"

    MILITARY_SERVICES = CANDIDATE + "/military_services"
    MILITARY_SERVICE = MILITARY_SERVICES + "/%s"

    PHONES = CANDIDATE + "/phones"
    PHONE = PHONES + "/%s"

    PREFERRED_LOCATIONS = CANDIDATE + "/preferred_locations"
    PREFERRED_LOCATION = PREFERRED_LOCATIONS + "/%s"

    SKILLS = CANDIDATE + "/skills"
    SKILL = SKILLS + "/%s"

    SOCIAL_NETWORKS = CANDIDATE + "/social_networks"
    SOCIAL_NETWORK = SOCIAL_NETWORKS + "/%s"

    WORK_PREFERENCE = CANDIDATE + "/work_preference/%s"
    CANDIDATE_EDIT = CANDIDATE + "/edits"


class SchedulerApiUrl(object):
    """
    Rest URLs of scheduler_service
    """
    HOST_NAME = _get_host_name(GTApis.SCHEDULER_SERVICE_NAME,
                               GTApis.SCHEDULER_SERVICE_PORT)
    TASKS = HOST_NAME % '/tasks/'
    TASK = HOST_NAME % '/tasks/id/%s'

"""
This file contains API REST endpoints of all services e.g. one of the endpoint of auth_service is
    /v1/oauth2/token.

This also contains complete URLs of REST endpoints of all services. e.g. for above example,
complete URL will be 127.0.0.1:8011/v1/oauth2/token

Here we have two(or maybe three) classes for each service.
 e.g. for candidate_service
 1) CandidateApi which contains REST endpoints
 2) CandidateApiUrl which contains complete URLs of REST endpoints
 3) CandidateApiWords which contains common words for both above classes.

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
            http://auth-service-staging.gettalent.com (for auth service)
    For PROD:
            http://auth-service.gettalent.com (for auth service)

    :param service_name: Name of service
    :param port_number: Port number of service
    :type service_name: str
    :type port_number: int
    :return:
    """
    env = os.getenv(TalentConfigKeys.ENV_KEY) or 'dev'
    if env in ['dev', 'circle']:
        # This looks like http://127.0.0.1:8001 (for auth service)
        return LOCAL_HOST + ':' + str(port_number) + '%s'
    elif env == 'qa':
        # This looks like https://auth-service-webdev.gettalent.com (for auth service)
        return 'https://' + service_name + '-staging' + TALENT_DOMAIN + '%s'
    elif env == 'prod':
        # This looks like https://auth-service.gettalent.com (for auth service)
        return 'https://' + service_name + TALENT_DOMAIN + '%s'
    else:
        raise Exception("Environment variable GT_ENVIRONMENT not set correctly: Should be dev, circle, qa, or prod")


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
    EMAIL_CAMPAIGN_SERVICE_PORT = 8014

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
    EMAIL_CAMPAIGN_SERVICE_NAME = 'email-campaign-service'


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


class UserServiceApiWords(object):
    """
    This class contains words used for endpoints of user_service API.
    """
    USERS = 'users'
    DOMAINS = 'domains'
    DOMAIN = 'domain'
    ROLES = '/roles'
    GROUPS = 'groups'
    RESET_PASSWORD = '/reset_password'
    UPDATE_PASSWORD = '/update_password'
    FORGOT_PASSWORD = '/forgot_password'


class UserServiceApi(object):
    """
    API relative URLs for user_service. e.g. /v1/users
    """
    VERSION = 'v1'
    USERS = UserServiceApiWords.USERS
    DOMAINS = UserServiceApiWords.DOMAINS
    URL_PREFIX = _get_url_prefix(VERSION)
    _GROUP = UserServiceApiWords.GROUPS + '/<int:group_id>/'
    USER = UserServiceApiWords.USERS + "/<int:id>"
    DOMAIN = UserServiceApiWords.DOMAINS + "/<int:id>"
    USER_ROLES = UserServiceApiWords.USERS + "/<int:user_id>" + UserServiceApiWords.ROLES
    DOMAIN_ROLES = UserServiceApiWords.DOMAIN + '/<int:domain_id>' + UserServiceApiWords.ROLES
    DOMAIN_GROUPS = UserServiceApiWords.DOMAIN + "/<int:domain_id>/" + UserServiceApiWords.GROUPS
    DOMAIN_GROUPS_UPDATE = UserServiceApiWords.DOMAIN + "/" + UserServiceApiWords.GROUPS + '/<int:group_id>'
    USER_GROUPS = _GROUP + UserServiceApiWords.USERS
    UPDATE_PASSWORD = UserServiceApiWords.USERS + UserServiceApiWords.UPDATE_PASSWORD
    FORGOT_PASSWORD = UserServiceApiWords.USERS + UserServiceApiWords.FORGOT_PASSWORD
    RESET_PASSWORD = UserServiceApiWords.USERS + UserServiceApiWords.RESET_PASSWORD + '/<token>'


class UserServiceApiUrl(object):
    """
    Rest URLs of user_service
    """
    HOST_NAME = _get_host_name(GTApis.USER_SERVICE_NAME,
                               GTApis.USER_SERVICE_PORT)
    HEALTH_CHECK = _get_health_check_url(HOST_NAME)
    API_URL = HOST_NAME % _get_api_relative_version(UserServiceApi.VERSION)
    USERS = API_URL % UserServiceApiWords.USERS
    USER = USERS + '/%s'
    DOMAINS = API_URL % UserServiceApiWords.DOMAINS
    DOMAIN = DOMAINS + '/%s'
    USER_ROLES_API = API_URL % (UserServiceApiWords.USERS + '/%s' + UserServiceApiWords.ROLES)
    DOMAIN_ROLES_API = API_URL % (UserServiceApiWords.DOMAIN + '/%s' + UserServiceApiWords.ROLES)
    DOMAIN_GROUPS_API = API_URL % (UserServiceApiWords.DOMAIN + '/%s/' + UserServiceApiWords.GROUPS)
    DOMAIN_GROUPS_UPDATE_API = API_URL % (UserServiceApiWords.DOMAIN + '/' + UserServiceApiWords.GROUPS + '/%s')
    USER_GROUPS_API = API_URL % (UserServiceApiWords.GROUPS + '/%s/' + UserServiceApiWords.USERS)
    UPDATE_PASSWORD_API = API_URL % UserServiceApi.UPDATE_PASSWORD
    FORGOT_PASSWORD_API = API_URL % UserServiceApi.FORGOT_PASSWORD
    RESET_PASSWORD_API = USERS + UserServiceApiWords.RESET_PASSWORD + '/%s'


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
    DOMAINS = API_URL % WidgetApi.DOMAINS
    UNIVERSITIES = API_URL % WidgetApi.UNIVERSITIES


class SocialNetworkApiUrl(object):
    """
    API relative URLs for social_network_service
    """
    HOST_NAME = _get_host_name(GTApis.SOCIAL_NETWORK_SERVICE_NAME,
                               GTApis.SOCIAL_NETWORK_SERVICE_PORT)
    HEALTH_CHECK = _get_health_check_url(HOST_NAME)


class CandidatePoolApiWords(object):
    """
    This class contains words used for endpoints of candidate_pool API.
    """
    TALENT_POOLS = 'talent-pools'
    TALENT_POOL = 'talent-pool'
    TALENT_PIPELINES = 'talent-pipelines'
    TALENT_PIPELINE = 'talent-pipeline'
    STATS = '/stats'
    CANDIDATES = '/candidates'
    GROUPS = 'groups'
    SMART_LISTS = '/smart_lists'


class CandidatePoolApi(object):
    """
    API relative URLs for candidate_pool_service. e.g. /v1/smartlists
    """
    VERSION = 'v1'
    # /v1/
    URL_PREFIX = _get_url_prefix(VERSION)
    _INT_ID = '/<int:id>'
    # Talent Pools
    TALENT_PIPELINES = CandidatePoolApiWords.TALENT_PIPELINES
    TALENT_POOLS = CandidatePoolApiWords.TALENT_POOLS
    TALENT_POOL = CandidatePoolApiWords.TALENT_POOLS + _INT_ID
    TALENT_POOL_CANDIDATES = TALENT_POOL + CandidatePoolApiWords.CANDIDATES
    TALENT_POOL_GROUPS = CandidatePoolApiWords.GROUPS + '/<int:group_id>/' + CandidatePoolApiWords.TALENT_POOLS
    TALENT_POOL_STATS = CandidatePoolApiWords.TALENT_POOLS + CandidatePoolApiWords.STATS
    TALENT_POOL_GET_STATS = CandidatePoolApiWords.TALENT_POOL + '/<int:talent_pool_id>' + CandidatePoolApiWords.STATS
    # Talent Pipelines1
    TALENT_PIPELINE = CandidatePoolApiWords.TALENT_PIPELINES + _INT_ID
    TALENT_PIPELINE_SMARTLISTS = CandidatePoolApiWords.TALENT_PIPELINE + _INT_ID + CandidatePoolApiWords.SMART_LISTS
    TALENT_PIPELINE_CANDIDATES = CandidatePoolApiWords.TALENT_PIPELINE + _INT_ID + CandidatePoolApiWords.CANDIDATES
    TALENT_PIPELINE_STATS = CandidatePoolApiWords.TALENT_PIPELINES + CandidatePoolApiWords.STATS
    TALENT_PIPELINE_GET_STATS = CandidatePoolApiWords.TALENT_PIPELINE + '/<int:talent_pipeline_id>' + CandidatePoolApiWords.STATS
    # Smartlists
    SMARTLISTS = 'smartlists'
    SMARTLIST = SMARTLISTS + _INT_ID
    SMARTLIST_CANDIDATES = SMARTLISTS + '/<int:smartlist_id>' + CandidatePoolApiWords.CANDIDATES
    SMARTLIST_STATS = SMARTLISTS + CandidatePoolApiWords.STATS
    SMARTLIST_GET_STATS = SMARTLISTS + '/<int:smartlist_id>' + CandidatePoolApiWords.STATS


class CandidatePoolApiUrl(object):
    """
    Rest URLs of candidate_pool_service
    """
    HOST_NAME = _get_host_name(GTApis.CANDIDATE_POOL_SERVICE_NAME,
                               GTApis.CANDIDATE_POOL_SERVICE_PORT)
    HEALTH_CHECK = _get_health_check_url(HOST_NAME)
    API_URL = HOST_NAME % _get_api_relative_version(CandidatePoolApi.VERSION)
    # Talent Pool
    TALENT_POOLS = API_URL % CandidatePoolApiWords.TALENT_POOLS
    TALENT_POOL = TALENT_POOLS + '/%s'
    TALENT_POOL_STATS = API_URL % CandidatePoolApi.TALENT_POOL_STATS
    TALENT_POOL_GET_STATS = API_URL % (CandidatePoolApiWords.TALENT_POOL+"/%s"+CandidatePoolApiWords.STATS)
    TALENT_POOL_CANDIDATE = API_URL % (CandidatePoolApiWords.TALENT_POOLS +'/%s'+CandidatePoolApiWords.CANDIDATES)
    TALENT_POOL_GROUP = API_URL % (CandidatePoolApiWords.GROUPS+'/%s/'+CandidatePoolApiWords.TALENT_POOLS)
    # Talent Pipeline
    TALENT_PIPELINES = API_URL % CandidatePoolApiWords.TALENT_PIPELINES
    TALENT_PIPELINE = TALENT_PIPELINES + '/%s'
    TALENT_PIPELINE_STATS = API_URL % CandidatePoolApi.TALENT_PIPELINE_STATS
    TALENT_PIPELINE_CANDIDATE = API_URL % (CandidatePoolApiWords.TALENT_PIPELINE+'/%s'+CandidatePoolApiWords.CANDIDATES)
    TALENT_PIPELINE_SMARTLISTS = API_URL % (CandidatePoolApiWords.TALENT_PIPELINE+'/%s'+CandidatePoolApiWords.SMART_LISTS)
    TALENT_PIPELINE_GET_STATS = API_URL % (CandidatePoolApiWords.TALENT_PIPELINE+"/%s"+CandidatePoolApiWords.STATS)
    # Smartlists
    SMARTLISTS = API_URL % CandidatePoolApi.SMARTLISTS
    SMARTLIST_STATS = API_URL % CandidatePoolApi.SMARTLIST_STATS
    SMARTLIST_GET_STATS = SMARTLISTS + "/%s" + CandidatePoolApiWords.STATS
    SMARTLIST_CANDIDATES = SMARTLISTS + '/%s' + CandidatePoolApiWords.CANDIDATES


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


class CandidateApiWords(object):
    """
    This class contains words used for endpoints of Candidate API.
    """
    CANDIDATES = "candidates"
    ADDRESSES = "/addresses"
    AOIS = "/areas_of_interest"
    CUSTOM_FIELD = "/custom_fields"
    EDUCATIONS = "/educations"
    DEGREES = "/degrees"
    BULLETS = "/bullets"
    EXPERIENCES = "/experiences"
    EMAILS = "/emails"
    MILITARY_SERVICES = "/military_services"
    PHONES = "/phones"
    PREFERRED_LOCATIONS = "/preferred_locations"
    SKILLS = "/skills"
    SOCIAL_NETWORKS = "/social_networks"
    WORK_PREFERENCES = "/work_preference"
    EDITS = "/edits"
    SEARCH = "/search"
    DOCUMENTS = "/documents"
    OPENWEB = '/openweb'


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

    CANDIDATES = RELATIVE_VERSION % CandidateApiWords.CANDIDATES
    _CANDIDATE_ID = CANDIDATES + "/<int:candidate_id>"
    CANDIDATE_ID = RELATIVE_VERSION % (CandidateApiWords.CANDIDATES + _INT_ID)
    CANDIDATE_EMAIL = RELATIVE_VERSION % (CandidateApiWords.CANDIDATES + "/<email>")

    ADDRESSES = _CANDIDATE_ID + CandidateApiWords.ADDRESSES
    ADDRESS = ADDRESSES + _INT_ID

    AOIS = _CANDIDATE_ID + CandidateApiWords.AOIS
    AOI = AOIS + _INT_ID

    CUSTOM_FIELDS = _CANDIDATE_ID + CandidateApiWords.CUSTOM_FIELD
    CUSTOM_FIELD = CUSTOM_FIELDS + _INT_ID

    EDUCATIONS = _CANDIDATE_ID + CandidateApiWords.EDUCATIONS
    EDUCATION = EDUCATIONS + _INT_ID

    DEGREES = EDUCATIONS + '/<int:education_id>' + CandidateApiWords.DEGREES
    DEGREE = DEGREES + _INT_ID

    DEGREE_BULLETS = DEGREES + "/<int:degree_id>" + CandidateApiWords.BULLETS
    DEGREE_BULLET = DEGREE_BULLETS + _INT_ID

    EXPERIENCES = _CANDIDATE_ID + CandidateApiWords.EXPERIENCES
    EXPERIENCE = EXPERIENCES + _INT_ID

    EXPERIENCE_BULLETS = EXPERIENCES + "/<int:experience_id>" + CandidateApiWords.BULLETS
    EXPERIENCE_BULLET = EXPERIENCE_BULLETS + _INT_ID

    EMAILS = _CANDIDATE_ID + CandidateApiWords.EMAILS
    EMAIL = EMAILS + _INT_ID

    MILITARY_SERVICES = _CANDIDATE_ID + CandidateApiWords.MILITARY_SERVICES
    MILITARY_SERVICE = MILITARY_SERVICES + _INT_ID

    PHONES = _CANDIDATE_ID + CandidateApiWords.PHONES
    PHONE = PHONES + _INT_ID

    PREFERRED_LOCATIONS = _CANDIDATE_ID + CandidateApiWords.PREFERRED_LOCATIONS
    PREFERRED_LOCATION = PREFERRED_LOCATIONS + _INT_ID

    SKILLS = _CANDIDATE_ID + CandidateApiWords.SKILLS
    SKILL = SKILLS + _INT_ID

    SOCIAL_NETWORKS = _CANDIDATE_ID + CandidateApiWords.SOCIAL_NETWORKS
    SOCIAL_NETWORK = SOCIAL_NETWORKS + _INT_ID

    WORK_PREFERENCE = _CANDIDATE_ID + CandidateApiWords.WORK_PREFERENCES + _INT_ID
    CANDIDATE_EDIT = CANDIDATE_ID + CandidateApiWords.EDITS

    CANDIDATE_SEARCH = CANDIDATES + CandidateApiWords.SEARCH
    CANDIDATES_DOCUMENTS = CANDIDATES + CandidateApiWords.DOCUMENTS
    OPENWEB = CANDIDATES + CandidateApiWords.OPENWEB


class CandidateApiUrl(object):
    """
    Rest URLs of candidate_service
    """
    HOST_NAME = _get_host_name(GTApis.CANDIDATE_SERVICE_NAME,
                               GTApis.CANDIDATE_SERVICE_PORT)
    HEALTH_CHECK = _get_health_check_url(HOST_NAME)
    CANDIDATES = HOST_NAME % CandidateApi.CANDIDATES
    CANDIDATE = CANDIDATES + "/%s"

    ADDRESSES = CANDIDATE + CandidateApiWords.ADDRESSES
    ADDRESS = ADDRESSES + "/%s"

    AOIS = CANDIDATE + CandidateApiWords.AOIS
    AOI = AOIS + "/%s"

    CUSTOM_FIELDS = CANDIDATE + CandidateApiWords.CUSTOM_FIELD
    CUSTOM_FIELD = CUSTOM_FIELDS + "/%s"

    CANDIDATE_SEARCH_URI = CANDIDATES + CandidateApiWords.SEARCH

    CANDIDATES_DOCUMENTS_URI = CANDIDATES + CandidateApiWords.DOCUMENTS

    EDUCATIONS = CANDIDATE + CandidateApiWords.EDUCATIONS
    EDUCATION = EDUCATIONS + "/%s"

    DEGREES = EDUCATION + CandidateApiWords.DEGREES
    DEGREE = DEGREES + "/%s"

    DEGREE_BULLETS = DEGREE + CandidateApiWords.BULLETS
    DEGREE_BULLET = DEGREE_BULLETS + "/%s"

    EMAILS = CANDIDATE + CandidateApiWords.EMAILS
    EMAIL = EMAILS + "/%s"

    EXPERIENCES = CANDIDATE + CandidateApiWords.EXPERIENCES
    EXPERIENCE = EXPERIENCES + "/%s"

    EXPERIENCE_BULLETS = EXPERIENCE + CandidateApiWords.BULLETS
    EXPERIENCE_BULLET = EXPERIENCE_BULLETS + "/%s"

    MILITARY_SERVICES = CANDIDATE + CandidateApiWords.MILITARY_SERVICES
    MILITARY_SERVICE = MILITARY_SERVICES + "/%s"

    PHONES = CANDIDATE + CandidateApiWords.PHONES
    PHONE = PHONES + "/%s"

    PREFERRED_LOCATIONS = CANDIDATE + CandidateApiWords.PREFERRED_LOCATIONS
    PREFERRED_LOCATION = PREFERRED_LOCATIONS + "/%s"

    SKILLS = CANDIDATE + CandidateApiWords.SKILLS
    SKILL = SKILLS + "/%s"

    SOCIAL_NETWORKS = CANDIDATE + CandidateApiWords.SOCIAL_NETWORKS
    SOCIAL_NETWORK = SOCIAL_NETWORKS + "/%s"

    WORK_PREFERENCE = CANDIDATE + CandidateApiWords.WORK_PREFERENCES + "/%s"
    CANDIDATE_EDIT = CANDIDATE + CandidateApiWords.EDITS


class SchedulerApi(object):
    """
    Rest Relative URLs of scheduler_service
    """

    VERSION = 'v1'

    # URLs, in case of API
    RELATIVE_VERSION = _get_api_relative_version(VERSION)
    SCHEDULER_MULTIPLE_TASKS = RELATIVE_VERSION % "tasks/"
    SCHEDULER_TASKS_TEST = RELATIVE_VERSION % "tasks/test/"
    SCHEDULER_ONE_TASK = RELATIVE_VERSION % "tasks/id/<string:_id>"
    SCHEDULER_NAMED_TASK = RELATIVE_VERSION % "tasks/name/<string:_name>"
    SCHEDULER_ONE_TASK_NAME = RELATIVE_VERSION % "tasks/name/<string:_name>"
    SCHEDULER_MULTIPLE_TASK_RESUME = RELATIVE_VERSION % "tasks/resume/"
    SCHEDULER_MULTIPLE_TASK_PAUSE = RELATIVE_VERSION % "tasks/pause/"
    SCHEDULER_SINGLE_TASK_RESUME = RELATIVE_VERSION % "tasks/<string:_id>/resume/"
    SCHEDULER_SINGLE_TASK_PAUSE = RELATIVE_VERSION % "tasks/<string:_id>/pause/"


class SchedulerApiUrl(object):
    """
    Rest URLs of scheduler_service
    """
    HOST_NAME = _get_host_name(GTApis.SCHEDULER_SERVICE_NAME,
                               GTApis.SCHEDULER_SERVICE_PORT)

    VERSION = 'v1'

    HOST_NAME %= _get_api_relative_version(VERSION)
    # URLs, in case of test cases
    TASKS = HOST_NAME % "tasks/"
    TASK = HOST_NAME % 'tasks/id/%s'
    TASK_NAME = HOST_NAME % 'tasks/name/%s'
    PAUSE_TASK = HOST_NAME % 'tasks/%s/pause/'
    RESUME_TASK = HOST_NAME % 'tasks/%s/resume/'
    PAUSE_TASKS = HOST_NAME % 'tasks/pause/'
    RESUME_TASKS = HOST_NAME % 'tasks/resume/'
    TEST_TASK = HOST_NAME % 'tasks/test/'

    # Use different port of scheduler service URL
    FLOWER_MONITORING = '--port=5511'


class EmailCampaignEndpoints(object):
    VERSION = 'v1'
    RELATIVE_VERSION = _get_api_relative_version(VERSION)
    EMAIL_CAMPAIGNS = RELATIVE_VERSION % 'email-campaigns'
    EMAIL_CAMPAIGN = RELATIVE_VERSION % 'email-campaigns/<int:id>'
    SEND_CAMPAIGNS = RELATIVE_VERSION % 'email-campaigns/send'


class EmailCampaignUrl(object):
    VERSION = 'v1'
    HOST_NAME = _get_host_name(GTApis.EMAIL_CAMPAIGN_SERVICE_NAME,
                               GTApis.EMAIL_CAMPAIGN_SERVICE_PORT)
    EMAIL_CAMPAIGNS = HOST_NAME % EmailCampaignEndpoints.EMAIL_CAMPAIGNS
    EMAIL_CAMPAIGN = HOST_NAME % EmailCampaignEndpoints.EMAIL_CAMPAIGNS + "/%s"
    SEND_CAMPAIGNS = HOST_NAME % EmailCampaignEndpoints.SEND_CAMPAIGNS

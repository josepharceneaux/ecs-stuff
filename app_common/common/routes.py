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
from talent_config_manager import TalentConfigKeys, TalentEnvs

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
    :return:  A string that looks like https://auth-service.gettalent.com%s
    """
    env = os.getenv(TalentConfigKeys.ENV_KEY) or TalentEnvs.DEV
    if env == TalentEnvs.DEV:
        # This looks like http://127.0.0.1:8001 (for auth service)
        return LOCAL_HOST + ':' + str(port_number) + '%s'
    elif env == TalentEnvs.JENKINS:
        return 'http://jenkins.gettalent.com' + ':' + str(port_number) + '%s'
    elif env == TalentEnvs.QA:
        # This looks like:  https://auth-service-staging.gettalent.com%s
        return 'https://' + service_name + '-staging' + TALENT_DOMAIN + '%s'
    elif env == TalentEnvs.PROD:
        # This looks like: https://auth-service.gettalent.com%s
        return 'https://' + service_name + TALENT_DOMAIN + '%s'
    else:
        raise Exception("Environment variable GT_ENVIRONMENT not set correctly: "
                        "Should be %s, %s, %s or %s"
                        % (TalentEnvs.DEV, TalentEnvs.JENKINS, TalentEnvs.QA, TalentEnvs.PROD))


def get_web_app_url():
    env = os.getenv(TalentConfigKeys.ENV_KEY) or TalentEnvs.DEV
    if env in (TalentEnvs.DEV, TalentEnvs.JENKINS):
        return LOCAL_HOST + ':3000'
    elif env == TalentEnvs.QA:
        return 'https://staging.gettalent.com'
    elif env == TalentEnvs.PROD:
        return 'https://app.gettalent.com'
    else:
        raise Exception("Environment variable GT_ENVIRONMENT not set correctly: "
                        "Should be %s, %s, %s or %s"
                        % (TalentEnvs.DEV, TalentEnvs.JENKINS, TalentEnvs.QA, TalentEnvs.PROD))


def _get_api_relative_version(api_version):
    """
    Given version of API, this returns e.g. /v1/%s
    :param (str) api_version: version of API. e.g. v1 or v2 etc
    """
    return '/%s/%s' % (api_version, '%s')


def _get_url_prefix(api_version):
    """
    For given API version this gives url_prefix to be used for API registration
    e.g if api_version is v1, it will return /v1/
    :param (str) api_version: version of API
    """
    return '/' + api_version + '/'


def _get_health_check_url(host_name):
    """
    This returns the healthcheck url appended with host name. e.g.http://127.0.0.1:8001/healthcheck
    :param (str) host_name: name of host. e.g.http://127.0.0.1:8001
    """
    return host_name % HEALTH_CHECK


def _get_modified_route(route):
    """
    This function will give us the route for a particular resource to be used in tests.
    Input:
    >>> '/candidates/<int:id>/phones/<int:phone_id>'
    Output:
    >>> '/candidates/%s/phones/%s'
    """
    new_sub_str = []
    for sub_str in route.split('/'):
        if sub_str.startswith('<'):
            new_sub_str.append('%s')
        else:
            new_sub_str.append(sub_str)
    if route.startswith('/'):
        return '/'.join(new_sub_str)
    else:
        return new_sub_str[0] + '/' + '/'.join(new_sub_str[1::])


class GTApis(object):
    """
    This class contains the getTalent flask micro services' name and respective port numbers.
    """
    # Port Numbers of Flask micro services
    AUTH_SERVICE_PORT = 8001
    ACTIVITY_SERVICE_PORT = 8002
    RESUME_PARSING_SERVICE_PORT = 8003
    USER_SERVICE_PORT = 8004
    CANDIDATE_SERVICE_PORT = 8005
    WIDGET_SERVICE_PORT = 8006
    SOCIAL_NETWORK_SERVICE_PORT = 8007
    CANDIDATE_POOL_SERVICE_PORT = 8008
    SPREADSHEET_IMPORT_SERVICE_PORT = 8009
    DASHBOARD_SERVICE_PORT = 8010
    SCHEDULER_SERVICE_PORT = 8011
    SMS_CAMPAIGN_SERVICE_PORT = 8012
    PUSH_CAMPAIGN_SERVICE_PORT = 8013
    EMAIL_CAMPAIGN_SERVICE_PORT = 8014

    # Names of flask micro services
    AUTH_SERVICE_NAME = 'auth-service'
    ACTIVITY_SERVICE_NAME = 'activity-service'
    RESUME_PARSING_SERVICE_NAME = 'resume-parsing-service'
    USER_SERVICE_NAME = 'user-service'
    CANDIDATE_SERVICE_NAME = 'candidate-service'
    WIDGET_SERVICE_NAME = 'widget-service'
    SOCIAL_NETWORK_SERVICE_NAME = 'social-network-service'
    CANDIDATE_POOL_SERVICE_NAME = 'candidate-pool-service'
    SPREADSHEET_IMPORT_SERVICE_NAME = 'spreadsheet-import-service'
    DASHBOARD_SERVICE_NAME = 'frontend-service'
    SCHEDULER_SERVICE_NAME = 'scheduler-service'
    SMS_CAMPAIGN_SERVICE_NAME = 'sms-campaign-service'
    PUSH_CAMPAIGN_SERVICE_NAME = 'push-campaign-service'
    EMAIL_CAMPAIGN_SERVICE_NAME = 'email-campaign-service'

    # CORS headers
    CORS_HEADERS = {r"*": {"origins": [r".*\.gettalent\.com",
                                       "http://127.0.0.1",
                                       "https://127.0.0.1",
                                       "http://localhost"]}}


class AuthApiRoutes(object):
    """
    API relative URLs for auth_service. e.g. /v1/oauth2/token
    It also returns Rest URLs of auth_service

    ** Usage **
    >>> AuthApiRoutes(url=False).TOKEN_CREATE
    /v1/oauth2/token

    >>> AuthApiRoutes().TOKEN_CREATE
    https://127.0.0.1:8001/v1/oauth2/token
    """
    VERSION = 'v1'
    RELATIVE_VERSION = _get_api_relative_version(VERSION)
    HOST_NAME = _get_host_name(GTApis.AUTH_SERVICE_NAME, GTApis.AUTH_SERVICE_PORT)
    HEALTH_CHECK = _get_health_check_url(HOST_NAME)

    def __init__(self, url=True):
        initial_str = self.HOST_NAME if url else '%s'
        self.TOKEN_CREATE = initial_str % self.RELATIVE_VERSION % 'oauth2/token'
        self.TOKEN_REVOKE = initial_str % self.RELATIVE_VERSION % 'oauth2/revoke'
        self.AUTHORIZE = initial_str % self.RELATIVE_VERSION % 'oauth2/authorize'


class AuthApiV2(object):
    """
    API relative URLs for auth_service. e.g. /v1/oauth2/token
    """
    VERSION = 'v2'
    RELATIVE_VERSION = _get_api_relative_version(VERSION)
    TOKEN_CREATE = RELATIVE_VERSION % 'oauth2/token'
    TOKEN_REFRESH = RELATIVE_VERSION % 'oauth2/refresh'
    TOKEN_REVOKE = RELATIVE_VERSION % 'oauth2/revoke'
    AUTHORIZE = RELATIVE_VERSION % 'oauth2/authorize'


class AuthApiUrlV2(object):
    """
    Rest URLs of auth_service
    """
    HOST_NAME = _get_host_name(GTApis.AUTH_SERVICE_NAME,
                               GTApis.AUTH_SERVICE_PORT)
    HEALTH_CHECK = _get_health_check_url(HOST_NAME)
    TOKEN_CREATE = HOST_NAME % AuthApiV2.TOKEN_CREATE
    TOKEN_REFRESH = HOST_NAME % AuthApiV2.TOKEN_REFRESH
    TOKEN_REVOKE = HOST_NAME % AuthApiV2.TOKEN_REVOKE
    AUTHORIZE = HOST_NAME % AuthApiV2.AUTHORIZE


class ActivityApi(object):
    """
    API relative URLs for activity_service. e.g /v1/activities/
    """
    VERSION = 'v1'
    # /v1/activities/
    ACTIVITIES = '/' + VERSION + '/activities/'
    # /v1/activities/<page>
    ACTIVITIES_PAGE = '/' + VERSION + '/activities/<page>'
    ACTIVITY_MESSAGES = '/' + VERSION + '/messages'
    LAST_READ = '/' + VERSION + '/last-read'


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
    API relative URLs for resume_parsing_service. e.g. /v1/parse_resume
    """
    VERSION = 'v1'
    URL_PREFIX = _get_url_prefix(VERSION)
    RELATIVE_VERSION = _get_api_relative_version(VERSION)
    PARSE = 'parse_resume'
    BATCH = 'batch'


class ResumeApiUrl(object):
    """
    Rest URLs of resume_parsing_service
    """
    HOST_NAME = _get_host_name(GTApis.RESUME_PARSING_SERVICE_NAME,
                               GTApis.RESUME_PARSING_SERVICE_PORT)
    HEALTH_CHECK = _get_health_check_url(HOST_NAME)
    API_URL = HOST_NAME % ResumeApi.RELATIVE_VERSION
    PARSE = API_URL % ResumeApi.PARSE
    BATCH_URL = API_URL % ResumeApi.BATCH
    BATCH_PROCESS = '{}/{}'.format(BATCH_URL, '<int:user_id>')


class UserServiceApi(object):
    """
    API relative URLs for user_service. e.g. /v1/users
    """
    VERSION = 'v1'
    URL_PREFIX = _get_url_prefix(VERSION)
    USERS = "users"
    USER = "users/<int:id>"
    DOMAINS = "domains"
    DOMAIN = "domains/<int:id>"
    USER_ROLES = "users/<int:user_id>/roles"
    DOMAIN_ROLES = "domain/<int:domain_id>/roles"
    DOMAIN_GROUPS = "domain/<int:domain_id>/groups"
    DOMAIN_GROUPS_UPDATE = "domain/groups/<int:group_id>"
    USER_GROUPS = "groups/<int:group_id>/users"
    UPDATE_PASSWORD = "users/update-password"
    FORGOT_PASSWORD = "users/forgot-password"
    RESET_PASSWORD = "users/reset-password/<token>"

    DOMAIN_SOURCES = '/' + VERSION + '/sources'
    DOMAIN_SOURCE = '/' + VERSION + '/sources/<int:id>'
    DOMAIN_CUSTOM_FIELDS = '/' + VERSION + '/custom_fields'


class UserServiceApiUrl(object):
    """
    Rest URLs of user_service
    """
    HOST_NAME = _get_host_name(GTApis.USER_SERVICE_NAME,
                               GTApis.USER_SERVICE_PORT)
    HEALTH_CHECK = _get_health_check_url(HOST_NAME)
    API_URL = HOST_NAME % _get_api_relative_version(UserServiceApi.VERSION)
    USERS = API_URL % 'users'
    USER = API_URL % 'users/%s'
    DOMAINS = API_URL % "domains"
    DOMAIN = API_URL % "domains/%s"
    USER_ROLES_API = API_URL % 'users/%s/roles'
    DOMAIN_ROLES_API = API_URL % 'domain/%s/roles'
    DOMAIN_GROUPS_API = API_URL % 'domain/%s/groups'
    DOMAIN_GROUPS_UPDATE_API = API_URL % 'domain/groups/%s'

    DOMAIN_SOURCES = API_URL % "sources"
    DOMAIN_SOURCE = API_URL % "sources/%s"

    USER_GROUPS_API = API_URL % "groups/%s/users"
    UPDATE_PASSWORD_API = API_URL % UserServiceApi.UPDATE_PASSWORD
    FORGOT_PASSWORD_API = API_URL % UserServiceApi.FORGOT_PASSWORD
    RESET_PASSWORD_API = USERS + '/reset-password/%s'
    DOMAIN_CUSTOM_FIELDS = API_URL % "custom_fields"


class CandidateApi(object):
    """
    API relative URLs for candidate_service. e.g /v1/candidates
    """
    VERSION = 'v1'
    HOST_NAME = _get_host_name(GTApis.CANDIDATE_SERVICE_NAME, GTApis.CANDIDATE_SERVICE_PORT)
    HEALTH_CHECK = _get_health_check_url(HOST_NAME)

    CANDIDATES = '/' + VERSION + '/candidates'
    CANDIDATE_ID = '/' + VERSION + '/candidates/<int:id>'
    CANDIDATE_EMAIL = '/' + VERSION + '/candidates/<email>'

    ADDRESSES = '/' + VERSION + '/candidates/<int:candidate_id>/addresses'
    ADDRESS = '/' + VERSION + '/candidates/<int:candidate_id>/addresses/<int:id>'

    AOIS = '/' + VERSION + '/candidates/<int:candidate_id>/areas_of_interest'
    AOI = '/' + VERSION + '/candidates/<int:candidate_id>/areas_of_interest/<int:id>'

    CUSTOM_FIELDS = '/' + VERSION + '/candidates/<int:candidate_id>/custom_fields'
    CUSTOM_FIELD = '/' + VERSION + '/candidates/<int:candidate_id>/custom_fields/<int:id>'

    EDUCATIONS = '/' + VERSION + '/candidates/<int:candidate_id>/educations'
    EDUCATION = '/' + VERSION + '/candidates/<int:candidate_id>/educations/<int:id>'

    DEGREES = '/' + VERSION + '/candidates/<int:candidate_id>/educations/<int:education_id>/degrees'
    DEGREE = '/' + VERSION + '/candidates/<int:candidate_id>/educations/<int:education_id>/degrees/<int:id>'

    DEGREE_BULLETS = '/' + VERSION + '/candidates/<int:candidate_id>/educations/<int:education_id>/degrees/<int:degree_id>/bullets'
    DEGREE_BULLET = '/' + VERSION + '/candidates/<int:candidate_id>/educations/<int:education_id>/degrees/<int:degree_id>/bullets/<int:id>'

    DEVICES = '/' + VERSION + '/candidates/<int:id>/devices'
    DEVICE = '/' + VERSION + '/candidates/<int:id>/devices/<int:id>'

    EXPERIENCES = '/' + VERSION + '/candidates/<int:candidate_id>/work_experiences'
    EXPERIENCE = '/' + VERSION + '/candidates/<int:candidate_id>/work_experiences/<int:id>'

    EXPERIENCE_BULLETS = '/' + VERSION + '/candidates/<int:candidate_id>/work_experiences/<int:experience_id>/bullets'
    EXPERIENCE_BULLET = '/' + VERSION + '/candidates/<int:candidate_id>/work_experiences/<int:experience_id>/bullets/<int:id>'

    EMAILS = '/' + VERSION + '/candidates/<int:candidate_id>/emails'
    EMAIL = '/' + VERSION + '/candidates/<int:candidate_id>/emails/<int:id>'

    MILITARY_SERVICES = '/' + VERSION + '/candidates/<int:candidate_id>/military_services'
    MILITARY_SERVICE = '/' + VERSION + '/candidates/<int:candidate_id>/military_services/<int:id>'

    PHONES = '/' + VERSION + '/candidates/<int:candidate_id>/phones'
    PHONE = '/' + VERSION + '/candidates/<int:candidate_id>/phones/<int:id>'

    PREFERRED_LOCATIONS = '/' + VERSION + '/candidates/<int:candidate_id>/preferred_locations'
    PREFERRED_LOCATION = '/' + VERSION + '/candidates/<int:candidate_id>/preferred_locations/<int:id>'

    SKILLS = '/' + VERSION + '/candidates/<int:candidate_id>/skills'
    SKILL = '/' + VERSION + '/candidates/<int:candidate_id>/skills/<int:id>'

    PHOTOS = '/' + VERSION + '/candidates/<int:candidate_id>/photos'
    PHOTO = '/' + VERSION + '/candidates/<int:candidate_id>/photos/<int:id>'

    SOCIAL_NETWORKS = '/' + VERSION + '/candidates/<int:candidate_id>/social_networks'
    SOCIAL_NETWORK = '/' + VERSION + '/candidates/<int:candidate_id>/social_networks/<int:id>'

    WORK_PREFERENCES = '/' + VERSION + '/candidates/<int:candidate_id>/work_preferences'
    WORK_PREFERENCE = '/' + VERSION + '/candidates/<int:candidate_id>/work_preferences/<int:id>'
    CANDIDATE_EDIT = '/' + VERSION + '/candidates/<int:id>/edits'

    CANDIDATE_SEARCH = '/' + VERSION + '/candidates/search'
    CANDIDATES_DOCUMENTS = '/' + VERSION + '/candidates/documents'
    OPENWEB = '/' + VERSION + '/candidates/openweb'
    CANDIDATE_CLIENT_CAMPAIGN = '/' + VERSION + '/candidates/client_email_campaign'
    CANDIDATE_VIEWS = '/' + VERSION + '/candidates/<int:id>/views'
    CANDIDATE_PREFERENCES = '/' + VERSION + '/candidates/<int:id>/preferences'
    CANDIDATE_NOTES = '/' + VERSION + '/candidates/<int:id>/notes'

    LANGUAGES = '/' + VERSION + '/candidates/<int:candidate_id>/languages'
    LANGUAGE = '/' + VERSION + '/candidates/<int:candidate_id>/languages/<int:id>'

    REFERENCES = '/' + VERSION + '/candidates/<int:candidate_id>/references'
    REFERENCE = '/' + VERSION + '/candidates/<int:candidate_id>/references/<int:id>'

    TAGS = '/' + VERSION + '/candidates/<int:candidate_id>/tags'
    TAG = '/' + VERSION + '/candidates/<int:candidate_id>/tags/<int:id>'

    PIPELINES = '/' + VERSION + '/candidates/<int:candidate_id>/pipelines'


class CandidateApiUrl(object):
    """
    Rest URLs of candidate_service
    """
    HOST_NAME = _get_host_name(GTApis.CANDIDATE_SERVICE_NAME,
                               GTApis.CANDIDATE_SERVICE_PORT)
    HEALTH_CHECK = _get_health_check_url(HOST_NAME)
    CANDIDATES = HOST_NAME % CandidateApi.CANDIDATES
    CANDIDATE = CANDIDATES + "/%s"

    ADDRESSES = HOST_NAME % _get_modified_route(CandidateApi.ADDRESSES)
    ADDRESS = HOST_NAME % _get_modified_route(CandidateApi.ADDRESS)

    AOIS = CANDIDATE + '/areas_of_interest'
    AOI = AOIS + "/%s"

    CUSTOM_FIELDS = CANDIDATE + '/custom_fields'
    CUSTOM_FIELD = CUSTOM_FIELDS + "/%s"

    CANDIDATE_SEARCH_URI = CANDIDATES + '/search'

    CANDIDATES_DOCUMENTS_URI = CANDIDATES + '/documents'

    EDUCATIONS = CANDIDATE + '/educations'
    EDUCATION = EDUCATIONS + "/%s"

    DEGREES = EDUCATION + '/degrees'
    DEGREE = DEGREES + "/%s"

    DEGREE_BULLETS = DEGREE + '/bullets'
    DEGREE_BULLET = DEGREE_BULLETS + "/%s"

    DEVICES = CANDIDATE + '/devices'
    DEVICE = DEVICES + '/%s'

    EMAILS = CANDIDATE + '/emails'
    EMAIL = EMAILS + "/%s"

    EXPERIENCES = CANDIDATE + '/work_experiences'
    EXPERIENCE = EXPERIENCES + "/%s"

    EXPERIENCE_BULLETS = EXPERIENCE + '/bullets'
    EXPERIENCE_BULLET = EXPERIENCE_BULLETS + "/%s"

    MILITARY_SERVICES = CANDIDATE + '/military_services'
    MILITARY_SERVICE = MILITARY_SERVICES + "/%s"

    PHONES = CANDIDATE + '/phones'
    PHONE = PHONES + "/%s"

    PREFERRED_LOCATIONS = CANDIDATE + '/preferred_locations'
    PREFERRED_LOCATION = PREFERRED_LOCATIONS + "/%s"

    SKILLS = CANDIDATE + '/skills'
    SKILL = SKILLS + "/%s"

    PHOTOS = CANDIDATE + '/photos'
    PHOTO = PHOTOS + "/%s"

    SOCIAL_NETWORKS = CANDIDATE + '/social_networks'
    SOCIAL_NETWORK = SOCIAL_NETWORKS + "/%s"

    WORK_PREFERENCES = CANDIDATE + '/work_preferences'
    WORK_PREFERENCE_ID = WORK_PREFERENCES + "/%s"
    CANDIDATE_EDIT = CANDIDATE + '/edits'
    CANDIDATE_VIEW = CANDIDATE + '/views'
    CANDIDATE_PREFERENCE = CANDIDATE + '/preferences'
    NOTES = CANDIDATE + '/notes'

    CANDIDATE_CLIENT_CAMPAIGN = CANDIDATES + '/client_email_campaign'

    LANGUAGES = CANDIDATE + '/languages'
    LANGUAGE = LANGUAGES + "/%s"

    REFERENCES = CANDIDATE + '/references'
    REFERENCE = REFERENCES + "/%s"

    TAGS = CANDIDATE + '/tags'
    TAG = TAGS + "/%s"

    PIPELINES = CANDIDATE + '/pipelines'

 
class WidgetApi(object):
    """
    API relative URLs for widget_service. e.g. /v1/universities
    """
    VERSION = 'v1'
    URL_PREFIX = _get_url_prefix(VERSION)
    DOMAINS = 'domains'
    DOMAIN_WIDGETS = 'domains/<path:encrypted_domain_id>/widgets/<path:encrypted_widget_id>'
    DOMAIN_INTERESTS = 'domains/<path:encrypted_domain_id>/interests'
    DOMAIN_MAJORS = 'domains/<path:encrypted_domain_id>/majors'
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


class CandidatePoolApi(object):
    """
    API relative URLs for candidate_pool_service. e.g. /v1/smartlists
    """
    VERSION = 'v1'
    # /v1/
    URL_PREFIX = _get_url_prefix(VERSION)
    # Talent Pools
    TALENT_PIPELINES = 'talent-pipelines'
    TALENT_POOLS = 'talent-pools'
    TALENT_POOL = 'talent-pools/<int:id>'
    TALENT_POOL_CANDIDATES = 'talent-pools/<int:id>/candidates'
    TALENT_PIPELINES_OF_TALENT_POOLS = 'talent-pools/<int:id>/candidates'
    TALENT_POOL_GROUPS = 'groups/<int:group_id>/talent-pools'
    TALENT_POOL_UPDATE_STATS = 'talent-pools/stats'
    TALENT_POOL_GET_STATS = 'talent-pools/<int:talent_pool_id>/stats'
    TALENT_PIPELINES_IN_TALENT_POOL_GET_STATS = 'talent-pools/<int:talent_pool_id>/talent-pipelines/stats'
    # Talent Pipelines
    TALENT_PIPELINE = 'talent-pipelines/<int:id>'
    TALENT_PIPELINE_SMARTLISTS = 'talent-pipelines/<int:id>/smartlists'
    TALENT_PIPELINE_CANDIDATES = 'talent-pipelines/<int:id>/candidates'
    TALENT_PIPELINE_CAMPAIGNS = 'talent-pipelines/<int:id>/campaigns'
    TALENT_PIPELINE_UPDATE_STATS = 'talent-pipelines/stats'
    TALENT_PIPELINE_GET_STATS = 'talent-pipelines/<int:talent_pipeline_id>/stats'
    # Smartlists
    SMARTLISTS = 'smartlists'
    SMARTLIST = 'smartlists/<int:id>'
    SMARTLIST_CANDIDATES = 'smartlists/<int:smartlist_id>/candidates'
    SMARTLIST_UPDATE_STATS = 'smartlists/stats'
    SMARTLIST_GET_STATS = 'smartlists/<int:smartlist_id>/stats'
    SMARTLIST_IN_TALENT_PIPELINE_GET_STATS = 'talent-pipelines/<int:talent_pipeline_id>/smartlists/stats'


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
    TALENT_POOL = API_URL % _get_modified_route(CandidatePoolApi.TALENT_POOL)
    TALENT_POOL_UPDATE_STATS = API_URL % CandidatePoolApi.TALENT_POOL_UPDATE_STATS
    TALENT_POOL_GET_STATS = API_URL % _get_modified_route(CandidatePoolApi.TALENT_PIPELINE_GET_STATS)
    TALENT_PIPELINES_IN_TALENT_POOL_GET_STATS = API_URL % _get_modified_route(CandidatePoolApi.TALENT_PIPELINES_IN_TALENT_POOL_GET_STATS)
    TALENT_POOL_CANDIDATE = API_URL % _get_modified_route(CandidatePoolApi.TALENT_POOL_CANDIDATES)
    TALENT_POOL_GROUP = API_URL % _get_modified_route(CandidatePoolApi.TALENT_POOL_GROUPS)
    TALENT_PIPELINES_OF_TALENT_POOLS = API_URL % _get_modified_route(CandidatePoolApi.TALENT_PIPELINES_OF_TALENT_POOLS)
    # Talent Pipeline
    TALENT_PIPELINES = API_URL % CandidatePoolApi.TALENT_PIPELINES
    TALENT_PIPELINE = API_URL % _get_modified_route(CandidatePoolApi.TALENT_PIPELINE)
    TALENT_PIPELINE_UPDATE_STATS = API_URL % CandidatePoolApi.TALENT_PIPELINE_UPDATE_STATS
    TALENT_PIPELINE_CANDIDATE = API_URL % _get_modified_route(CandidatePoolApi.TALENT_PIPELINE_CANDIDATES)
    TALENT_PIPELINE_CAMPAIGN = API_URL % _get_modified_route(CandidatePoolApi.TALENT_PIPELINE_CAMPAIGNS)
    TALENT_PIPELINE_SMARTLISTS = API_URL % _get_modified_route(CandidatePoolApi.TALENT_PIPELINE_SMARTLISTS)
    TALENT_PIPELINE_GET_STATS = API_URL % _get_modified_route(CandidatePoolApi.TALENT_PIPELINE_GET_STATS)
    # Smartlists
    SMARTLISTS = API_URL % CandidatePoolApi.SMARTLISTS
    SMARTLIST = API_URL % _get_modified_route(CandidatePoolApi.SMARTLIST)
    SMARTLIST_UPDATE_STATS = API_URL % CandidatePoolApi.SMARTLIST_UPDATE_STATS
    SMARTLIST_GET_STATS = API_URL % _get_modified_route(CandidatePoolApi.SMARTLIST_GET_STATS)
    SMARTLIST_CANDIDATES = API_URL % _get_modified_route(CandidatePoolApi.SMARTLIST_CANDIDATES)


class SpreadsheetImportApi(object):
    """
    API relative URLs for spreadsheet_import_service. e.g. /v1/parse_spreadsheet/convert_to_table
    """
    VERSION = 'v1'
    # This is /v1/
    URL_PREFIX = _get_url_prefix(VERSION)
    CONVERT_TO_TABLE = 'parse_spreadsheet/convert_to_table'
    IMPORT_CANDIDATES = 'parse_spreadsheet/import_candidates'


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


class SchedulerApi(object):
    """
    Rest Relative URLs of scheduler_service
    """

    VERSION = 'v1'

    # URLs, in case of API
    RELATIVE_VERSION = _get_api_relative_version(VERSION)
    SCHEDULER_MULTIPLE_TASKS = RELATIVE_VERSION % "tasks"
    SCHEDULER_TASKS_TEST = RELATIVE_VERSION % "tasks/test"
    SCHEDULER_ONE_TASK = RELATIVE_VERSION % "tasks/id/<string:_id>"
    SCHEDULER_NAMED_TASK = RELATIVE_VERSION % "tasks/name/<string:_name>"
    SCHEDULER_ONE_TASK_NAME = RELATIVE_VERSION % "tasks/name/<string:_name>"
    SCHEDULER_MULTIPLE_TASK_RESUME = RELATIVE_VERSION % "tasks/resume"
    SCHEDULER_MULTIPLE_TASK_PAUSE = RELATIVE_VERSION % "tasks/pause"
    SCHEDULER_SINGLE_TASK_RESUME = RELATIVE_VERSION % "tasks/<string:_id>/resume"
    SCHEDULER_SINGLE_TASK_PAUSE = RELATIVE_VERSION % "tasks/<string:_id>/pause"
    SCHEDULER_ADMIN_TASKS = RELATIVE_VERSION % "admin/tasks"


class SchedulerApiUrl(object):
    """
    Rest URLs of scheduler_service
    """
    HOST_NAME = _get_host_name(GTApis.SCHEDULER_SERVICE_NAME,
                               GTApis.SCHEDULER_SERVICE_PORT)

    VERSION = 'v1'

    RELATIVE_VERSION = HOST_NAME % _get_api_relative_version(VERSION)

    HEALTH_CHECK = _get_health_check_url(HOST_NAME)
    # URLs, in case of test cases
    TASKS = RELATIVE_VERSION % "tasks"
    TASK = RELATIVE_VERSION % 'tasks/id/%s'
    TASK_NAME = RELATIVE_VERSION % 'tasks/name/%s'
    PAUSE_TASK = RELATIVE_VERSION % 'tasks/%s/pause'
    RESUME_TASK = RELATIVE_VERSION % 'tasks/%s/resume'
    PAUSE_TASKS = RELATIVE_VERSION % 'tasks/pause'
    RESUME_TASKS = RELATIVE_VERSION % 'tasks/resume'
    TEST_TASK = RELATIVE_VERSION % 'tasks/test'

    # Scheduler Admin API
    ADMIN_TASKS = RELATIVE_VERSION % "admin/tasks"

    # Use different port of scheduler service URL
    FLOWER_MONITORING_PORT = '--port=5511'


class SocialNetworkApi(object):
    """
    Rest URLs for social_network_service
    """
    VERSION = 'v1'
    # URLs, in case of API
    RELATIVE_VERSION = _get_api_relative_version(VERSION)
    EVENTS = RELATIVE_VERSION % 'events'
    EVENT = RELATIVE_VERSION % 'events/<int:event_id>'
    SOCIAL_NETWORKS = RELATIVE_VERSION % 'social-networks'
    MEETUP_GROUPS = RELATIVE_VERSION % 'social-networks/meetup-groups'
    TOKEN_VALIDITY = RELATIVE_VERSION % 'social-networks/<int:social_network_id>/token/validity'
    TOKEN_REFRESH = RELATIVE_VERSION % 'social-networks/<int:social_network_id>/token/refresh'
    USER_SOCIAL_NETWORK_CREDENTIALS = RELATIVE_VERSION % 'social-networks/<int:social_network_id>/user/credentials'
    VENUES = RELATIVE_VERSION % 'venues'
    VENUE = RELATIVE_VERSION % 'venues/<int:venue_id>'
    EVENT_ORGANIZERS = RELATIVE_VERSION % 'event-organizers'
    EVENT_ORGANIZER = RELATIVE_VERSION % 'event-organizers/<int:organizer_id>'
    TIMEZONES = RELATIVE_VERSION % 'data/timezones'
    RSVP = RELATIVE_VERSION % 'rsvp'
    CODE = RELATIVE_VERSION % 'code'


class SocialNetworkApiUrl(object):
    """
    API relative URLs for social_network_service
    """
    HOST_NAME = _get_host_name(GTApis.SOCIAL_NETWORK_SERVICE_NAME,
                               GTApis.SOCIAL_NETWORK_SERVICE_PORT)
    HEALTH_CHECK = _get_health_check_url(HOST_NAME)

    # TODO: Make this URL dynamic i.e different for staging, dev or prod
    UI_APP_URL = 'http://localhost:3000'
    API_URL = HOST_NAME % _get_api_relative_version(SocialNetworkApi.VERSION)
    EVENTS = API_URL % 'events'
    EVENT = API_URL % 'events/%s'
    SOCIAL_NETWORKS = API_URL % 'social-networks'
    VENUES = API_URL % 'venues'
    VENUE = API_URL % 'venues/%s'
    EVENT_ORGANIZERS = API_URL % 'event-organizers'
    EVENT_ORGANIZER = API_URL % 'event-organizers/%s'
    TIMEZONES = API_URL % 'data/timezones'
    MEETUP_GROUPS = API_URL % 'social-networks/meetup-groups'
    TOKEN_VALIDITY = API_URL % 'social-networks/%s/token/validity'
    TOKEN_REFRESH = API_URL % 'social-networks/%s/token/refresh'
    USER_SOCIAL_NETWORK_CREDENTIALS = API_URL % 'social-networks/%s/user/credentials'
    RSVP = API_URL % 'rsvp'
    CODE = API_URL % 'code'


class CampaignWords(object):
    """
    This class contains words used for endpoints of SMS Campaign API.
    """
    CAMPAIGNS = 'campaigns'
    SCHEDULE = '/schedule'
    REDIRECT = 'redirect'
    RECEIVE = 'receive'
    SENDS = '/sends'
    SEND = '/send'
    BLASTS = '/blasts'
    REPLIES = '/replies'
    SMS_CAMPAIGNS = 'sms-' + CAMPAIGNS
    EMAIL_CAMPAIGNS = 'email-' + CAMPAIGNS


class SmsCampaignApi(object):
    """
    This class contains the REST endpoints of sms_campaign_service
    """
    VERSION = 'v1'
    # HOST_NAME is http://127.0.0.1:8012 for dev
    HOST_NAME = _get_host_name(GTApis.SMS_CAMPAIGN_SERVICE_NAME,
                               GTApis.SMS_CAMPAIGN_SERVICE_PORT)
    API_URL = '/%s/%s' % (VERSION, '%s')
    # endpoint /v1/sms-campaigns
    # GET all campaigns of a user, POST new campaign, DELETE campaigns of a user from given ids
    CAMPAIGNS = '/%s/%s' % (VERSION, CampaignWords.SMS_CAMPAIGNS)
    # endpoint /v1/sms-campaigns/:campaign_id
    # GET campaign by its id, POST: updates a campaign, DELETE a campaign from given id
    CAMPAIGN = CAMPAIGNS + '/<int:campaign_id>'
    # /v1/sms-campaigns/:campaign_id/schedule
    # To schedule an SMS campaign
    SCHEDULE = CAMPAIGN + CampaignWords.SCHEDULE
    # endpoint /v1/sms-campaigns/:campaign_id/send
    # To send a campaign to candidates
    SEND = CAMPAIGN + CampaignWords.SEND
    # endpoint /v1/redirect/:id
    # This endpoint is hit when candidate clicks on any URL present in SMS body text.
    REDIRECT = API_URL % (CampaignWords.REDIRECT + '/<int:url_conversion_id>')
    # endpoint /v1/receive
    # This endpoint is callback URL when candidate replies to a campaign via SMS
    RECEIVE = API_URL % CampaignWords.RECEIVE
    # endpoint /v1/sms-campaigns/:campaign_id/blasts
    # Gives the blasts of a campaign
    BLASTS = CAMPAIGN + CampaignWords.BLASTS
    # endpoint /v1/sms-campaigns/:campaign_id/blasts/:blast_id
    # Gives the blast object of SMS campaign from given blast id.
    BLAST = CAMPAIGN + CampaignWords.BLASTS + '/<int:blast_id>'
    # endpoint /v1/sms-campaigns/:campaign_id/blasts/:blast_id/sends
    # Gives the sends objects of a blast object of SMS campaign from given blast id.
    BLAST_SENDS = BLAST + CampaignWords.SENDS
    # endpoint /v1/sms-campaigns/:campaign_id/blasts/:blast_id/replies
    # Gives the replies objects of a blast object of SMS campaign from given blast id.
    BLAST_REPLIES = BLAST + CampaignWords.REPLIES
    # endpoint /v1/sms-campaigns/:campaign_id/sends
    # This gives the records from "sends" for a given id of campaign
    SENDS = CAMPAIGN + CampaignWords.SENDS
    # endpoint /v1/sms-campaigns/:campaign_id/replies
    # This gives the records from "sms_campaign_reply" for a given id of campaign
    REPLIES = CAMPAIGN + CampaignWords.REPLIES


class SmsCampaignApiUrl(object):
    """
    This class contains the REST URLs of sms_campaign_service
    """
    """ Endpoints' complete URLs for pyTests """
    CAMPAIGNS = SmsCampaignApi.HOST_NAME % SmsCampaignApi.CAMPAIGNS
    CAMPAIGN = CAMPAIGNS + '/%s'
    SCHEDULE = CAMPAIGN + CampaignWords.SCHEDULE
    SEND = CAMPAIGN + CampaignWords.SEND
    REDIRECT = SmsCampaignApi.HOST_NAME % '/%s/%s' % (SmsCampaignApi.VERSION,
                                                      CampaignWords.REDIRECT + '/%s')
    RECEIVE = SmsCampaignApi.HOST_NAME % SmsCampaignApi.RECEIVE
    BLASTS = CAMPAIGN + CampaignWords.BLASTS
    BLAST = BLASTS + '/%s'
    SENDS = CAMPAIGN + CampaignWords.SENDS
    REPLIES = CAMPAIGN + CampaignWords.REPLIES
    BLAST_SENDS = BLAST + CampaignWords.SENDS
    BLAST_REPLIES = BLAST + CampaignWords.REPLIES


class PushCampaignApi(object):
    """
    REST URLs for Push Campaign Service endpoints
    """
    VERSION = 'v1'

    API_URL = '/%s/%s' % (VERSION, '%s')
    # endpoint /v1/push-campaigns
    # GET all campaigns of a user, POST new campaign, DELETE campaigns of a user from given ids
    CAMPAIGNS = '/%s/%s' % (VERSION, 'push-campaigns')
    # endpoint /v1/push-campaigns/:id
    # GET campaign by its id, POST: updates a campaign, DELETE a campaign from given id
    CAMPAIGN = '/%s/%s' % (VERSION, 'push-campaigns/<int:campaign_id>')
    # endpoint /v1/push-campaigns/:id/sends
    # This gives the records from "sends" for a given id of campaign
    SENDS = CAMPAIGN + CampaignWords.SENDS
    BLASTS = CAMPAIGN + CampaignWords.BLASTS
    BLAST = BLASTS + '/<int:blast_id>'
    BLAST_SENDS = BLAST + CampaignWords.SENDS
    # endpoint /v1/push-campaigns/:id/send
    # To send a campaign to candidates
    SEND = CAMPAIGN + CampaignWords.SEND
    # /v1/push-campaigns/:id/schedule
    # To schedule a Push campaign
    SCHEDULE = CAMPAIGN + CampaignWords.SCHEDULE
    # endpoint /v1/redirect/:id
    # This endpoint is hit when candidate clicks on any URL present in Push campaign's body text.
    REDIRECT = API_URL % (CampaignWords.REDIRECT + '/<int:url_conversion_id>')

    # helper endpoints, need to get url_conversion records in some cases
    URL_CONVERSION = '/%s/%s/<int:_id>' % (VERSION, 'url-conversions')
    URL_CONVERSION_BY_SEND_ID = '/%s/%s/<int:send_id>' % (VERSION, 'send-url-conversions')


class PushCampaignApiUrl(object):
    """
    This class contains the REST URLs of push_campaign_service
    """
    """ Endpoints' complete URLs for pyTests """
    # HOST_NAME is http://127.0.0.1:8013 for dev
    HOST_NAME = _get_host_name(GTApis.PUSH_CAMPAIGN_SERVICE_NAME,
                               GTApis.PUSH_CAMPAIGN_SERVICE_PORT)
    CAMPAIGNS = HOST_NAME % PushCampaignApi.CAMPAIGNS
    CAMPAIGN = HOST_NAME % '/%s/%s' % (PushCampaignApi.VERSION, 'push-campaigns/%s')
    SENDS = CAMPAIGN + CampaignWords.SENDS
    BLASTS = CAMPAIGN + CampaignWords.BLASTS
    BLAST = BLASTS + '/%s'
    BLAST_SENDS = BLAST + CampaignWords.SENDS
    SEND = CAMPAIGN + CampaignWords.SEND
    SCHEDULE = CAMPAIGN + CampaignWords.SCHEDULE
    REDIRECT = HOST_NAME % '/%s/%s' % (PushCampaignApi.VERSION, 'redirect/%s')
    URL_CONVERSION = HOST_NAME % '/%s/%s' % (PushCampaignApi.VERSION, 'url-conversions/%s')
    URL_CONVERSION_BY_SEND_ID = HOST_NAME % '/%s/%s' % (PushCampaignApi.VERSION, 'send-url-conversions/%s')


class EmailCampaignEndpoints(object):
    VERSION = 'v1'

    HOST_NAME = _get_host_name(GTApis.EMAIL_CAMPAIGN_SERVICE_NAME,
                               GTApis.EMAIL_CAMPAIGN_SERVICE_PORT)
    RELATIVE_VERSION = _get_api_relative_version(VERSION)
    API_URL = '/%s/%s' % (VERSION, '%s')
    CAMPAIGNS = RELATIVE_VERSION % CampaignWords.EMAIL_CAMPAIGNS
    CAMPAIGN = CAMPAIGNS + '/<int:id>'
    # endpoint /v1/email-campaigns/:id/send
    # Send the campaign as specified by the id
    SEND = CAMPAIGNS + '/<int:campaign_id>' + CampaignWords.SEND
    URL_REDIRECT = API_URL % (CampaignWords.REDIRECT + '/<int:url_conversion_id>')
    # endpoint /v1/email-campaigns/:id/blasts
    # Gives the blasts of a campaign
    BLASTS = CAMPAIGNS + '/<int:campaign_id>' + CampaignWords.BLASTS
    # endpoint /v1/email-campaigns/:id/blasts/:id
    # Gives the blast object of a campaign for a particular blast_id
    BLAST = CAMPAIGNS + '/<int:campaign_id>' + CampaignWords.BLASTS + '/<int:blast_id>'
    # endpoint /v1/email-campaigns/:id/sends
    # Gives the sends of a campaign
    SENDS = CAMPAIGNS + '/<int:campaign_id>' + CampaignWords.SENDS
    # endpoint /v1/email-campaigns/:id/sends/:id
    # Gives the send object of a campaign for a particular send_id
    SEND_BY_ID = CAMPAIGNS + '/<int:campaign_id>' + CampaignWords.SENDS + '/<int:send_id>'


class EmailCampaignUrl(object):
    """
    This class contains URLs to be used in Py-tests
    """
    CAMPAIGNS = EmailCampaignEndpoints.HOST_NAME % EmailCampaignEndpoints.CAMPAIGNS
    CAMPAIGN = CAMPAIGNS + "/%s"
    SEND = CAMPAIGN + CampaignWords.SEND
    URL_REDIRECT = EmailCampaignEndpoints.HOST_NAME % ('/' + EmailCampaignEndpoints.VERSION
                                                       + '/' + CampaignWords.REDIRECT + '/%s')
    BLASTS = CAMPAIGN + CampaignWords.BLASTS
    BLAST = BLASTS + '/%s'

    TEMPLATES = EmailCampaignEndpoints.HOST_NAME % ('/' + EmailCampaignEndpoints.VERSION + '/email-templates')
    TEMPLATES_FOLDER = EmailCampaignEndpoints.HOST_NAME % ('/' + EmailCampaignEndpoints.VERSION +
                                                           '/email-template-folders')

    SENDS = CAMPAIGN + CampaignWords.SENDS
    SEND_BY_ID = SENDS + '/%s'

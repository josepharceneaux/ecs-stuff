"""
This file contains Base API URls of all services
"""


# GTDevBaseUrls
AUTH_SERVICE_API_URL = 'http://127.0.0.1:8001'
ACTIVITY_SERVICE_API_URL = 'http://127.0.0.1:8002'
RESUME_SERVICE_API_URL = 'http://127.0.0.1:8003'
USER_SERVICE_API_URL = 'http://127.0.0.1:8004'
CANDIDATE_SERVICE_API_URL = 'http://127.0.0.1:8005'
WIDGET_SERVICE_API_URL = 'http://127.0.0.1:8006'
SOCIAL_NETWORK_SERVICE_API_URL = 'http://127.0.0.1:8007'
SMS_CAMPAIGN_SERVICE_API_URL = 'http://127.0.0.1:8008'


class GTProdBaseUrls(object):
    """
    This class contains base API Urls of all services for production environment
    """
    def __init__(self):
        self.AUTH_SERVICE_API_URL = 'http://127.0.0.1:8001'
        self.ACTIVITY_SERVICE_API_URL = 'http://127.0.0.1:8002'
        self.RESUME_SERVICE_API_URL = 'http://127.0.0.1:8003'
        self.USER_SERVICE_API_URL = 'http://127.0.0.1:8004'
        self.CANDIDATE_SERVICE_API_URL = 'http://127.0.0.1:8005'
        self.WIDGET_SERVICE_API_URL = 'http://127.0.0.1:8006'
        self.SOCIAL_NETWORK_SERVICE_API_URL = 'http://127.0.0.1:8007'
        self.SMS_CAMPAIGN_SERVICE_API_URL = 'http://127.0.0.1:8008'

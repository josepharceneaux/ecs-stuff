"""
This file contains Base APP URls of all services
"""
from ..common_config import GT_ENVIRONMENT

if GT_ENVIRONMENT == 'dev':
    # GTDevBaseUrls
    AUTH_SERVICE_APP_URL = 'http://127.0.0.1:8001'
    ACTIVITY_SERVICE_APP_URL = 'http://127.0.0.1:8002'
    RESUME_SERVICE_APP_URL = 'http://127.0.0.1:8003'
    USER_SERVICE_APP_URL = 'http://127.0.0.1:8004'
    CANDIDATE_SERVICE_APP_URL = 'http://127.0.0.1:8005'
    WIDGET_SERVICE_APP_URL = 'http://127.0.0.1:8006'
    SOCIAL_NETWORK_SERVICE_APP_URL = 'http://127.0.0.1:8007'
    SMS_CAMPAIGN_SERVICE_APP_URL = 'http://127.0.0.1:8008'
elif GT_ENVIRONMENT == 'circle':
    pass
elif GT_ENVIRONMENT == 'qa':
    pass
elif GT_ENVIRONMENT == 'prod':
    pass
else:
    raise Exception("Environment variable GT_ENVIRONMENT not set correctly - could not run app.")

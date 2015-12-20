"""Run Sms Campaign Service APP"""

# Standard Library
import os

# Service Specific
from sms_campaign_service.sms_campaign_app.app import app

# Common Utils
from sms_campaign_service.common.routes import GTApis

if __name__ == '__main__':
    # TODO Have to remove this, only here for testing purposes
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    app.run(host='0.0.0.0', port=GTApis.SMS_CAMPAIGN_SERVICE_PORT, debug=False)

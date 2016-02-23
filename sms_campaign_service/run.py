"""Run Sms Campaign Service APP"""

# Service Specific
from sms_campaign_app.app import app

# Common Utils
from sms_campaign_service.common.routes import GTApis

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=GTApis.SMS_CAMPAIGN_SERVICE_PORT, debug=False)

"""Run Sms Campaign Service APP"""
from sms_campaign_service.app.app import app

import os

if __name__ == '__main__':
    # TODO Have to remove this, only here for testing purposes
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    app.run(host='0.0.0.0', port=8007, debug=False)

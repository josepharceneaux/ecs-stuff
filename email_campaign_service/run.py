import os
from email_campaign_app.app import app
from email_campaign_service.common.routes import GTApis

__author__ = 'jitesh'

if __name__ == '__main__':
    os.environ.setdefault('C_FORCE_ROOT', 'true')
    app.run(host='0.0.0.0', port=GTApis.EMAIL_CAMPAIGN_SERVICE_PORT, use_reloader=True, debug=False, threaded=True)

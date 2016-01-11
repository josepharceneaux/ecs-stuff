__author__ = 'ufarooqi'

import os
from auth_service.oauth import app
from auth_service.common.routes import GTApis

if __name__ == '__main__':
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    app.run(host='0.0.0.0', port=GTApis.AUTH_SERVICE_PORT, use_reloader=True, debug=False)

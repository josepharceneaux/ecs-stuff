"""Run Social Network Service APP"""
from social_network_service.app.app import app

import os
from social_network_service.common.routes import GTApis


if __name__ == '__main__':
    # TODO Have to remove this, only here for testing purposes
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    app.run(host='0.0.0.0', port=GTApis.SOCIAL_NETWORK_SERVICE_PORT, debug=False, threaded=True)

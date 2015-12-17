"""Run Social Network Service APP"""
import os
from social_network_service.app.app import app
from social_network_service.common.utils.app_rest_urls import GTApis

if __name__ == '__main__':
    # TODO Have to remove this, only here for testing purposes
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    app.run(host='0.0.0.0', port=GTApis.SOCIAL_NETWORK_SERVICE_PORT, debug=False)

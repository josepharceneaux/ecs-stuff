"""Run Social Network Service APP"""
from social_network_service.app.app import app

import os

if __name__ == '__main__':
    # TODO Have to remove this, only here for testing purposes
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    app.run(port=5000, debug=True)

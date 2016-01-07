__author__ = 'ufarooqi'

import os
from flask.ext.common.common.routes import GTApis
from candidate_pool_service.candidate_pool_app import app

if __name__ == '__main__':
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    app.run(host='0.0.0.0', port=GTApis.CANDIDATE_POOL_SERVICE_PORT, use_reloader=True, debug=False)

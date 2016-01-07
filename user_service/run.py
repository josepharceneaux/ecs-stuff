__author__ = 'ufarooqi'

from user_app import app
from flask.ext.common.common.routes import GTApis

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=GTApis.USER_SERVICE_PORT, use_reloader=True, debug=False)

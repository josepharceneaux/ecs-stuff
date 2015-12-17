__author__ = 'ufarooqi'

from user_app import app
from user_service.common.utils.app_rest_urls import GTApis


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=GTApis.USER_SERVICE_PORT, use_reloader=True, debug=False)

__author__ = 'ufarooqi'

import os

from spreadsheet_import_service.app import app
from widget_service.common.utils.app_rest_urls import GTApis


if __name__ == '__main__':
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    app.run(host='0.0.0.0', port=GTApis.SPREADSHEET_IMPORT_SERVICE_PORT, use_reloader=True, debug=False)

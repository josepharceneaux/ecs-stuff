__author__ = 'ufarooqi'

from spreadsheet_import_service.app import app
import os
from flask.ext.common.common.routes import GTApis

if __name__ == '__main__':
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    app.run(host='0.0.0.0', port=GTApis.SPREADSHEET_IMPORT_SERVICE_PORT, use_reloader=True, debug=False)

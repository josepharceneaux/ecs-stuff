__author__ = 'Joseph Arceneaux'

from ats_app import app
from ats_service.common.routes import GTApis

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=GTApis.ATS_SERVICE_PORT, use_reloader=True, debug=False)

from mock_service.mock_service_app.app import app
from mock_service.common.routes import GTApis

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=GTApis.MOCK_SERVICE_PORT, use_reloader=True, debug=False, threaded=True)

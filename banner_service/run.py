"""Local run file."""
from banner_service.app import app
from banner_service.common.routes import GTApis


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=GTApis.BANNER_SERVICE_PORT, debug=True)

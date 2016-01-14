"""Local run file."""
from resume_parsing_service.app import app
from resume_parsing_service.common.routes import GTApis


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=GTApis.RESUME_PARSING_SERVICE_PORT, debug=True)

"""Local run file."""
from resume_parsing_app import app
from flask.ext.common.common.routes import GTApis


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=GTApis.RESUME_SERVICE_PORT, debug=True)

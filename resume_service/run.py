"""Local run file."""

# from resume_parsing_app.views import api
from resume_parsing_app import app


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8003, debug=True)

"""Local run file."""
from email_template_service.email_template import app


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8010, use_reloader=True, debug=False)

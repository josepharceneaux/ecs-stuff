"""Local run file."""

from flask import Flask
from resume_parsing_app.views import api


app = Flask(__name__)
app.config.from_object('config')
app.register_blueprint(api.mod)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)

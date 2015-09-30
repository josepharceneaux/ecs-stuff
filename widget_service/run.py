"""Local runfile/uWSGI callable"""
__author__ = 'erikfarmer'


from flask import Flask
from widget_app.views import api


app = Flask(__name__, template_folder='widget_app/templates', static_folder='widget_app/static')
app.register_blueprint(api.mod, url_prefix='/widget')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8084, debug=True)
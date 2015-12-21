"""Local runfile/uWSGI callable"""
__author__ = 'erikfarmer'

from widget_app import app

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8007, debug=True)

__author__ = 'ufarooqi'

from auth_service.oauth import app

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8001, use_reloader=True, debug=False)
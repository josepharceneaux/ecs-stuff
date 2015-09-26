__author__ = 'ufarooqi'

from auth_service.oauth import app

if __name__ == '__main__':
    app.run(port=8081, use_reloader=False, debug=True)


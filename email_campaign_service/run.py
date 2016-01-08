from email_campaign_service.email_campaign_app import app

__author__ = 'jitesh'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8014, use_reloader=True, debug=False)

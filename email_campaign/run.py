from email_campaign import app
from common.talent_config import DEBUG

__author__ = 'jitesh'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8007, use_reloader=True, debug=DEBUG)

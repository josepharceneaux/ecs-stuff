"""
This modules run the service on specific port
"""
from push_campaign_app.app import app
from common.routes import GTApis

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=GTApis.PUSH_CAMPAIGN_SERVICE_PORT, debug=False)
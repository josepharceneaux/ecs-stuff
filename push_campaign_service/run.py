"""
This modules run the service on specific port
"""
from push_campaign_app.app import app
from push_campaign_service.common.routes import GTApis
from push_campaign_service.common.custom_contracts import define_custom_contracts

if __name__ == "__main__":
    define_custom_contracts()
    app.run(host="0.0.0.0", port=GTApis.PUSH_CAMPAIGN_SERVICE_PORT, debug=False)

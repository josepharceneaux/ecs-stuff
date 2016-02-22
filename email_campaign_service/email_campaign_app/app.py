from email_campaign_service.email_campaign_app import app

__author__ = 'basit'

# Register API endpoints
from apis.email_campaigns import email_campaign_blueprint
app.register_blueprint(email_campaign_blueprint)

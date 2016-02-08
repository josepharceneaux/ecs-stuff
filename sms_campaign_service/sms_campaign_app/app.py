"""
    Author: Hafiz Muhammad Basit, QC-Technologies, <basit.gettalent@gmail.com>

    This module contains sms_campaign_app startup.
    We register blueprints for different APIs with this app.
"""
# Imports for Blueprints
from api.v1_sms_campaign_api import sms_campaign_blueprint

# Register Blueprints for different APIs
from sms_campaign_service.sms_campaign_app import app
app.register_blueprint(sms_campaign_blueprint)


@app.route('/')
def root():
    return 'Welcome to SMS Campaign Service'


"""
Author: Hafiz Muhammad Basit, QC-Technologies,
        Lahore, Punjab, Pakistan <basit.gettalent@gmail.com>

    This file contains constants used in SMS campaign service.
"""
from sms_campaign_service.common.utils.app_rest_urls import SmsCampaignApiUrl

TWILIO = 'Twilio'
MOBILE_PHONE_LABEL = 'Mobile'  # for mobile phone
TWILIO_ACCOUNT_SID = "AC7f332b44c4a2d893d34e6b340dbbf73f"
TWILIO_AUTH_TOKEN = "09e1a6e40b9d6588f8a6050dea6bbd98"

# This is not a REST url, so not moving it to app_rest_urls.py
SMS_URL_REDIRECT = 'http://6b20c71b.ngrok.io' + SmsCampaignApiUrl.API_VERSION \
                   + '/campaigns/{}/url_redirection/{}/'

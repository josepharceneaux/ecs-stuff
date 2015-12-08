"""
Author: Hafiz Muhammad Basit, QC-Technologies,
        Lahore, Punjab, Pakistan <basit.gettalent@gmail.com>

    This file contains constants used in SMS campaign service.
"""

POOL_SIZE = 5
TWILIO = 'Twilio'
PHONE_LABEL_ID = 1  # for mobile phone
GOOGLE_API_KEY = 'AIzaSyCT7Gg3zfB0yXaBXSPNVhFCZRJzu9WHo4o'
GOOGLE_URL_SHORTENER_API_URL = 'https://www.googleapis.com/urlshortener/v1/url?key=' \
                               + GOOGLE_API_KEY

TWILIO_ACCOUNT_SID = "AC7f332b44c4a2d893d34e6b340dbbf73f"
TWILIO_AUTH_TOKEN = "09e1a6e40b9d6588f8a6050dea6bbd98"
SMS_URL_REDIRECT = 'http://6b20c71b.ngrok.io/campaigns/{}/url_redirection/{}/'

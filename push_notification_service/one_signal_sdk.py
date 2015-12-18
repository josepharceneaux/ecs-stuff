"""
This module contains code which implements Api calls for OneSignal Rest API.
"""
import json

import requests

CREATE_NOTIFICATION_URL = 'https://onesignal.com/api/v1/notifications'
GET_NOTIFICATIONS_URL = 'https://onesignal.com/api/v1/notifications?app_id=%s&limit=%s&offset=%s'
GET_NOTIFICATION_URL = 'https://onesignal.com/api/v1/notifications/%s?app_id=%s'


class OneSignalSdk(object):

    def __init__(self, app_id, rest_key):
        self.app_id = app_id
        self.rest_key = rest_key

    def create_app(self):
        pass

    def update_app(self):
        pass

    def get_apps(self):
        pass

    def get_app(self):
        pass

    def get_players(self):
        pass

    def get_player(self):
        pass

    def create_notification(self, url, message, title, **kwargs):
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Basic %s" % self.rest_key
        }

        segments = kwargs.get('segments')
        tags = kwargs.get('tags')
        data = {
            "app_id": self.app_id,
            "contents": {"en": message},
            "headings": {"en": title},
            "url": url,
            "include_player_ids": ["56c1d574-237e-4a41-992e-c0094b6f2ded"],
            "chrome_web_icon": "http://cdn.designcrowd.com.s3.amazonaws.com/blog/Oct2012/52-Startup-Logos-2012/SLR_0040_gettalent.jpg"
        }
        data = json.dumps(data)
        return send_request(CREATE_NOTIFICATION_URL, method='POST', data=data, headers=headers)

    def update_notification(self):
        pass

    def get_notifications(self):
        url = GET_NOTIFICATIONS_URL % self.app_id
        return send_request(url)

    def get_notification(self, _id):
        url = GET_NOTIFICATION_URL % (_id, self.app_id)
        return send_request(url)

    def delete_notification(self, _id):
        pass


def send_request(url, method='GET', data=None, headers=None):
    method = getattr(requests, method.lower())
    response = method(url=url, data=data, headers=headers)
    return response

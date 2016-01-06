"""
This module contains code which implements Api calls for OneSignal Rest API.
"""
import json

import requests

from constants import GET_TALENT_ICON_URL

CREATE_NOTIFICATION_URL = 'https://onesignal.com/api/v1/notifications'
GET_NOTIFICATIONS_URL = 'https://onesignal.com/api/v1/notifications?app_id=%s&limit=%s&offset=%s'
GET_NOTIFICATION_URL = 'https://onesignal.com/api/v1/notifications/%s?app_id=%s'
GET_PLAYERS_URL = 'https://onesignal.com/api/v1/players?app_id=%s&limit=%s&offset=%s'
GET_PLAYER_URL = 'https://onesignal.com/api/v1/players/%s'


class OneSignalSdk(object):

    def __init__(self, app_id, rest_key):
        self.app_id = app_id
        self.rest_key = rest_key
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": "Basic %s" % self.rest_key
        }

    def create_app(self):
        pass

    def update_app(self):
        pass

    def get_apps(self):
        pass

    def get_app(self):
        pass

    def get_players(self, limit=300, offset=0):
        url = GET_PLAYERS_URL % (self.app_id, limit, offset)
        return send_request(url, method='GET', headers=self.headers)

    def get_player(self, _id):
        url = GET_PLAYER_URL % _id
        return send_request(url, method='GET')

    def send_notification(self, url, message, name, players=None, **kwargs):

        segments = kwargs.get('segments')
        segments = segments if isinstance(segments, list) and len(segments) else ['All']
        tags = kwargs.get('tags')
        tags = tags if isinstance(tags, list) and len(tags) else None
        data = {
            "app_id": self.app_id,
            "contents": {"en": message},
            "headings": {"en": name},
            "url": url,
            "chrome_web_icon": GET_TALENT_ICON_URL
        }
        if players and isinstance(players, list):
            data['include_player_ids'] = players
        if tags:
            data['tags'] = tags

        # if not data.get('include_player_ids') and not data.get('tags'):
        #     data['included_segments'] = segments
        data = json.dumps(data)
        return send_request(CREATE_NOTIFICATION_URL, method='POST', data=data, headers=self.headers)

    def update_notification(self):
        pass

    def get_notifications(self, limit=50, offset=0):
        url = GET_NOTIFICATIONS_URL % (self.app_id, limit, offset)
        return send_request(url, method='GET', headers=self.headers)

    def get_notification(self, _id):
        url = GET_NOTIFICATION_URL % (_id, self.app_id)
        return send_request(url)

    def delete_notification(self, _id):
        pass


def send_request(url, method='GET', data=None, headers=None):
    method = getattr(requests, method.lower())
    response = method(url=url, data=data, headers=headers)
    return response

"""
Library for integrating with Workday accounts.
"""


import requests
import json


class Workday(object):
    """
    """

    def __init__(self, logger, ats_name, login_url, user_id, credentials):
        """
        """
        self.logger = logger
        self.ats_name = ats_name
        self.login_url = login_url
        self.user_id = user_id
        self.credentials = credentials
        self.fetch_candidates_url = "https://faux-workday.gettalent.com/all-individuals"
        self.fetch_individual_url = "https://faux-workday.gettalent.com/individual"

    def authenticate(self):
        """
        """
        pass

    def fetch_individual_references(self):
        """
        """
        self.logger.info("GET {}".format(self.fetch_candidates_url))
        response = requests.request('GET', self.fetch_candidates_url)
        return json.loads(response.text)

    def fetch_individual(self, reference):
        """
        """
        self.logger.info("GET {}".format(self.fetch_individual_url))
        response = requests.request('GET', self.fetch_individual_url + "/{}".format(reference))
        return response.text

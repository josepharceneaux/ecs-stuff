"""
Library for integrating with Workday accounts.
"""


import requests


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
        self.fetch_candidates = "https://faux-workday.gettalent.com/all-individuals"

    def authenticate(self):
        """
        """
        pass

    def fetch_individual_references(self):
        """
        """
        self.logger.info("GET {}".format(self.fetch_candidates))
        response = requests.request('GET', self.fetch_candidates)
        self.logger.info("Got: {}".format(response.text))
        return response.text

    def fetch_individual(self, reference):
        """
        """
        pass

"""
Functions related to candidate_service/candidate_app/api validations
"""
import json
from candidate_service.common.models.db import db
from candidate_service.common.models.candidate import Candidate
from candidate_service.common.models.candidate import CandidateSocialNetwork
from candidate_service.common.error_handling import InternalServerError
from candidate_service.common.error_handling import NotFoundError
import requests

SOCIALCV_API_KEY = "c96dfb6b9344d07cee29804152f798751ae8fdee"


def query_openweb(url):
    """
    Function search openweb endpoint for social network url
    :param url: social-network-url: string
    :return: json object
    """

    try:
        openweb_response = requests.get("http://api.thesocialcv.com/v3/profile/data.json", params=dict(apiKey=SOCIALCV_API_KEY, webProfile=url))
    except Exception as e:
        raise InternalServerError(error_message="Request error")

    if openweb_response.status_code == 404:
        raise NotFoundError(error_message="Candidate not found")

    if openweb_response.status_code != 200:
        raise InternalServerError(error_message="Response error")

    return openweb_response


def find_candidate_from_openweb(url):
    """
    Fetchs candidate profiles from openweb and compare it to local db
    :param url:
    :return: candidate sql query
    """
    openweb_response = query_openweb(url).json()
    urls = []
    if openweb_response:
        for candidate_url in openweb_response['webProfiles']:
            urls.append(openweb_response['webProfiles'][candidate_url]['url'])

    query = db.session.query(Candidate).join(CandidateSocialNetwork).filter(CandidateSocialNetwork.social_profile_url.in_(urls)).first()
    return query
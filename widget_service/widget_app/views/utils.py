__author__ = 'erikfarmer'

from widget_service.common.models.db import db
from widget_service.common.models.misc import AreaOfInterest


def parse_interest_ids_from_form(interests_string):
    processed_interest_ids = []
    raw_interests = interests_string.split('|')
    for interest in raw_interests:
        category, subcategroy = interest.split(':')
        subcategory = subcategroy.lstrip()
        interest_to_query = category if subcategroy == 'All Subcategories' else subcategory
        processed_interest_ids.append(
            {'id': db.query(AreaOfInterest.id).filter_by(
                AreaOfInterest.description==interest_to_query).first()})
    return processed_interest_ids
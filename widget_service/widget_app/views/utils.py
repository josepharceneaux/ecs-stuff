__author__ = 'erikfarmer'

from widget_service.widget_app import db
from widget_service.common.models.misc import AreaOfInterest


def parse_interest_ids_from_form(interests_string):
    processed_interest_ids = []
    raw_interests = interests_string.split('|')
    for interest in raw_interests:
        category, subcategory = interest.split(':')
        subcategory = subcategory.lstrip()
        interest_to_query = category if subcategory == 'All Subcategories' else subcategory
        processed_interest_ids.append(
            {'id': db.session.query(AreaOfInterest.id).filter(
                AreaOfInterest.description==interest_to_query).first().id})
    return processed_interest_ids
from flask import Blueprint
api_v2 = Blueprint('activities_api_v2', __name__)


# Create activities
@api_v2.route('/activities', methods=['POST'])
def create_activity():
    return 'create'


# Get list of domain activities excluding user for toasts
@api_v2.route('/activities', methods=['GET'])
def get_domain_activities():
    return 'domain'


# Get paginated domain activities for list page
@api_v2.route('/activities/<page>', methods=['GET'])
def get_paginated_activities(page):
    return 'domain paginated {}'.format(page)


# Get aggregated activities for drop down
@api_v2.route('/aggregate', methods=['GET'])
def get_aggregated_activities():
    return 'aggregated'

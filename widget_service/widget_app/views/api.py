"""Widget serving/processing"""
__author = 'erikfarmer'

# Standard library
import json
from collections import defaultdict

# Framework specific/Third Party
from flask import Blueprint
from flask import current_app as app
from flask import jsonify
from flask import request
from flask import render_template
import requests

# Module specific
from widget_service.common.models.candidate import CustomField
from widget_service.common.models.candidate import University
from widget_service.common.models.misc import AreaOfInterest
from widget_service.common.models.misc import Major
from widget_service.common.models.user import Domain
from widget_service.common.models.widget import WidgetPage
from widget_service.widget_app import db
from widget_service.widget_app.views.utils import parse_interest_ids_from_form
from widget_service.widget_app.views.utils import parse_city_and_state_ids_from_form
from widget_service.common.utils.db_utils import serialize_queried_sa_obj

mod = Blueprint('widget_api', __name__)


@mod.route('/widgets/<domain_uuid>', methods=['GET'])
def show_widget(domain_uuid):
    """ Route for testing template rendering/js functions/etc.
    :param domain: (string) the domain associated with an html template in for local testing.
    :return: a rendered HTML page.
    """
    template = db.session.query(WidgetPage).filter_by(domain_uuid=domain_uuid).first().template_name
    return render_template(template, domain=domain_uuid)


#TODO This should dynamically add 'optional' fields such as preferred location/military experience.
@mod.route('/widget/<domain>', methods=['POST'])
def create_candidate_from_widget(domain):
    """ Post receiver for processing widget date.
    :return: A success or error message to change the page state of a widget.
    """
    form = request.form
    candidate_dict = defaultdict(dict)
    candidate_dict['full_name'] = '{} {}'.format(form['firstName'], form['lastName'])
    candidate_dict['emails'] =  [{'address': form['emailAdd'], 'label': 'Primary'}]
    candidate_dict['areas_of_interest'] = parse_interest_ids_from_form(form['hidden-tags-aoi'])
    if form['hidden-tags-location']:
        custom_fields = parse_city_and_state_ids_from_form(form['hidden-tags-location'])
        candidate_dict.setdefault('custom_fields', []).append(custom_fields)
    if form['jobFrequency']:
        frequency_field = db.session.query(CustomField).filter_by(name='Subscription Preference').first()
        candidate_dict.setdefault('custom_fields', []).append(
            {frequency_field.id: form['jobFrequency']}
        )
    if form['militaryBranch']:
        candidate_dict['military_services']['branch'] = form['militaryBranch']
    if form['militaryStatus']:
        candidate_dict['military_services']['status'] = form['militaryStatus']
    if form['militaryGrade']:
        candidate_dict['military_services']['grade'] = form['militaryGrade']
    if form['militaryToDate']:
        candidate_dict['military_services']['to_date'] = form['militaryToDate']
    payload = json.dumps({'candidates': [candidate_dict]})
    try:
        r = requests.post(app.config['CANDIDATE_CREATION_URI'], data=payload,
                          headers={'Authorization': app.config['OAUTH_TOKEN'].access_token})
    except:
        return jsonify({'error': {'message': 'unable to create candidate from form'}})
    return jsonify({'success': {'message': 'candidate successfully created'}}), 201


@mod.route('/<domain_uuid>/interests', methods=['GET'])
def get_areas_of_interest(domain_uuid):
    """ API call that provides interests list filtered by the domain.
    :param domain: (string)
    :return: A dictionary pointing to primary and seconday interests that have been filtered by
             domain.
    """
    current_domain = db.session.query(Domain).filter_by(uuid=domain_uuid).first()
    interests = db.session.query(AreaOfInterest).filter(
        AreaOfInterest.domain_id == current_domain.id)
    primary_interests = []
    secondary_interests = []
    for interest in interests:
        if interest.parent_id:
            secondary_interests.append(serialize_queried_sa_obj(interest))
        else:
            primary_interests.append(serialize_queried_sa_obj(interest))
    return jsonify({'primary_interests': primary_interests,
                    'secondary_interests': secondary_interests})


@mod.route('/<domain_uuid>/majors', methods=['GET'])
def get_major_names(domain_uuid):
    """API call for returning list of major names filtered by domain"""
    domain_id = db.session.query(Domain.id).filter(Domain.uuid==domain_uuid)
    majors = db.session.query(Major).filter(domain_id==domain_id)
    return jsonify(majors=[serialize_queried_sa_obj(m) for m in majors])


@mod.route('/universities', methods=['GET'])
def get_university_names():
    """API call for names of universities in db in format used by widget select tags."""
    universities = db.session.query(University).all()
    return jsonify(universities_list=[serialize_queried_sa_obj(u) for u in universities])
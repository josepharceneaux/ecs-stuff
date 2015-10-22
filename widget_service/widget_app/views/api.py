"""Widget serving/processing"""
__author = 'erikfarmer'

# Standard library
import json
from collections import defaultdict
from datetime import datetime

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
from widget_service.widget_app.views.utils import create_candidate_educations_dict
from widget_service.widget_app.views.utils import parse_interest_ids_from_form
from widget_service.widget_app.views.utils import parse_city_and_state_ids_from_form
from widget_service.widget_app.views.utils import process_city_and_state_from_fields
from widget_service.common.utils.db_utils import serialize_queried_sa_obj
from widget_service.common.utils.auth_utils import get_token_by_client_and_user
from widget_service.common.utils.auth_utils import refresh_expired_token

from widget_service.widget_app.views.utils import get_widget_user_from_domain

mod = Blueprint('widget_api', __name__)


@mod.route('/widgets/<domain_uuid>', methods=['GET'])
def show_widget(domain_uuid):
    """ Route for testing template rendering/js functions/etc.
    :param domain_uuid: (string) the domain associated with an html template.
    :return: a rendered HTML page.
    """
    template = db.session.query(WidgetPage).filter_by(domain_uuid=domain_uuid).first().template_name
    return render_template(template, domain=domain_uuid)


@mod.route('/widgets/<domain_uuid>', methods=['POST'])
def create_candidate_from_widget(domain_uuid):
    """ Post receiver for processing widget date.
    :param domain_uuid: (string) the domain_uuid associated with a WidgetPage.
    :return: A success or error message to change the page state of a widget.
    """
    # Get User from domain
    widget_user_id = get_widget_user_from_domain(domain_uuid)
    # Get or Widget Client
    widget_client_id = app.config['WIDGET_CLIENT_ID']
    # Check for Token with userId and Client
    widget_token = get_token_by_client_and_user(widget_client_id, widget_user_id)
    # If expired refresh
    if widget_token.expires < datetime.now():
        access_token = refresh_expired_token(widget_token, widget_client_id,
                                             app.config['WIDGET_CLIENT_SECRET'])
    else:
        access_token = widget_token.access_token
    form = request.form
    candidate_dict = defaultdict(dict)
    # Common fields.
    candidate_single_field_name = form.get('name')
    candidate_double_field_name = '{} {}'.format(form.get('firstName'), form.get('lastName'))
    candidate_dict['emails'] = [{'address': form['emailAdd'], 'label': 'Primary'}]
    candidate_dict['areas_of_interest'] = parse_interest_ids_from_form(form['hidden-tags-aoi'])
    # Location based fields.
    candidate_locations = form.get('hidden-tags-location')
    candidate_city = form.get('city')
    candidate_state = form.get('state')
    # Education fields.
    candidate_university = form.get('university')
    candidate_degree = form.get('degree')
    candidate_major = form.get('major')
    candidate_graduation_date = form.get('graduation')
    # Kaiser University Only Field.
    candidate_nuid = form.get('nuid')
    # Kaiser Military fields.
    candidate_military_branch = form.get('militaryBranch')
    candidate_military_status = form.get('militaryStatus')
    candidate_military_grade = form.get('militaryGrade')
    candidate_military_to_date = form.get('militaryToDate')
    candidate_frequency = form.get('jobFrequency')
    # Common Widget field processing.
    if candidate_single_field_name:
        candidate_dict['full_name'] = candidate_single_field_name
    else:
        candidate_dict['full_name'] = candidate_double_field_name
    if candidate_locations:
        custom_fields = parse_city_and_state_ids_from_form(candidate_locations)
        candidate_dict.setdefault('custom_fields', []).extend(custom_fields)
    if candidate_city and candidate_state:
        city_state_list = process_city_and_state_from_fields(candidate_city, candidate_state)
        candidate_dict.setdefault('custom_fields', []).extend(city_state_list)
    if candidate_frequency:
        frequency_field = db.session.query(CustomField).filter_by(
            name='Subscription Preference').first()
        candidate_dict.setdefault('custom_fields', []).append(
            {'id': frequency_field.id, 'value': candidate_frequency}
        )
    # Kaiser University specific processing.
    if candidate_university and candidate_degree and candidate_major:
        candidate_dict['educations'] = [create_candidate_educations_dict(candidate_university,
                                                                        candidate_degree,
                                                                        candidate_major,
                                                                        candidate_graduation_date)]
    if candidate_nuid:
        nuid_field = db.session.query(CustomField).filter_by(name='NUID').first()
        candidate_dict.setdefault('custom_fields', []).append(
            {'id': nuid_field.id, 'value': candidate_nuid}
        )
    # Kaiser Military specific processing.
    military_service_dict = {}
    if candidate_military_branch:
        military_service_dict['branch'] = candidate_military_branch
    if candidate_military_status:
        military_service_dict['status'] = candidate_military_status
    if candidate_military_grade:
        military_service_dict['grade'] = candidate_military_grade
    if candidate_military_to_date:
        military_service_dict['to_date'] = candidate_military_to_date
    candidate_dict['military_services'] = [military_service_dict] if military_service_dict else None

    payload = json.dumps({'candidates': [candidate_dict]})
    r = requests.post(app.config['CANDIDATE_CREATION_URI'], data=payload,
                      headers={'Authorization': 'bearer {}'.format(access_token)})
    if r.status_code != 200:
        return jsonify({'error': {'message': 'unable to create candidate from form'}}), 401
    return jsonify({'success': {'message': 'candidate successfully created'}}), 201


@mod.route('/<domain_uuid>/interests', methods=['GET'])
def get_areas_of_interest(domain_uuid):
    """ API call that provides interests list filtered by the domain.
    :param domain_uuid: (string)
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
    domain_id = db.session.query(Domain.id).filter(Domain.uuid == domain_uuid)
    majors = db.session.query(Major).filter(domain_id == domain_id)
    return jsonify(majors=[serialize_queried_sa_obj(m) for m in majors])


@mod.route('/universities', methods=['GET'])
def get_university_names():
    """API call for names of universities in db in format used by widget select tags."""
    universities = db.session.query(University).all()
    return jsonify(universities_list=[serialize_queried_sa_obj(u) for u in universities])

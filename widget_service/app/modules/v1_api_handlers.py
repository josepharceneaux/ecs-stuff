__author__ = 'erik@gettalent'
import json
from collections import defaultdict

import requests
from flask import jsonify

from widget_service.app import db
from widget_service.app import logger
from widget_service.app.modules.utils import create_candidate_educations_dict
from widget_service.app.modules.utils import parse_city_and_state_ids_from_form
from widget_service.app.modules.utils import parse_interest_ids_from_form
from widget_service.app.modules.utils import process_city_and_state_from_fields
from widget_service.common.error_handling import InvalidUsage
from widget_service.common.models.misc import CustomField
from widget_service.common.models.talent_pools_pipelines import TalentPool
from widget_service.common.models.user import User
from widget_service.common.models.widget import WidgetPage
from widget_service.common.routes import CandidateApiUrl


def create_widget_candidate(form, talent_pool_hash):
    logger.info('WidgetService::FormInfo - {}'.format(form))
    talent_pool = TalentPool.get_by_simple_hash(talent_pool_hash)
    if not talent_pool:
        raise InvalidUsage(error_message='Unknown talent pool')
    domain_id = talent_pool.domain_id
    widget = WidgetPage.get_by_simple_hash(talent_pool_hash)
    if not widget:
        raise InvalidUsage(error_message='Unknown widget page')
    widget_user_id = widget.user_id
    widget_token = User.generate_jw_token(expiration=60, user_id=widget_user_id)

    candidate_dict = defaultdict(dict)
    # Common fields.
    candidate_single_field_name = form.get('name')
    candidate_double_field_name = '{} {}'.format(form.get('firstName'), form.get('lastName'))
    candidate_dict['emails'] = [{'address': form['emailAdd'], 'label': 'Primary'}]
    candidate_dict['areas_of_interest'] = parse_interest_ids_from_form(form['hidden-tags-aoi'], domain_id)
    # # Location based fields.
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
        custom_fields = parse_city_and_state_ids_from_form(candidate_locations, domain_id)
        candidate_dict.setdefault('custom_fields', []).extend(custom_fields)
    if candidate_city and candidate_state:
        city_state_list = process_city_and_state_from_fields(candidate_city, candidate_state, domain_id)
        candidate_dict.setdefault('custom_fields', []).extend(city_state_list)
    if candidate_frequency:
        frequency_field = db.session.query(CustomField).filter_by(
            name='Subscription Preference', domain_id=domain_id).first()
        candidate_dict.setdefault('custom_fields', []).append(
            {'custom_field_id': frequency_field.id, 'value': candidate_frequency}
        )

    # Kaiser University specific processing.
    if candidate_university and candidate_degree and candidate_major:
        candidate_dict['educations'] = [create_candidate_educations_dict(candidate_university,
                                                                        candidate_degree,
                                                                        candidate_major,
                                                                        candidate_graduation_date)]
    if candidate_nuid:
        nuid_field = db.session.query(CustomField).filter_by(name='NUID', domain_id=domain_id).first()
        candidate_dict.setdefault('custom_fields', []).append(
            {'custom_field_id': nuid_field.id, 'value': candidate_nuid}
        )
    # Kaiser Military specific processing.
    military_service_dict = {}
    if candidate_military_branch:
        military_service_dict['branch'] = candidate_military_branch
    if candidate_military_status:
        military_service_dict['status'] = candidate_military_status
    if candidate_military_grade:
        military_service_dict['highest_grade'] = candidate_military_grade
    if candidate_military_to_date:
        military_service_dict['to_date'] = candidate_military_to_date
    candidate_dict['military_services'] = [military_service_dict] if military_service_dict else None
    candidate_dict['talent_pool_ids']['add'] = [talent_pool.id]
    payload = json.dumps({'candidates': [candidate_dict]})
    r = requests.post(CandidateApiUrl.CANDIDATES, data=payload, headers={'Authorization': widget_token,
                                                                         'Content-Type': 'application/json'})
    if r.status_code != 201:
        return jsonify({'error': {'message': 'unable to create candidate from form'}}), 401
    return jsonify(candidate_dict), 201
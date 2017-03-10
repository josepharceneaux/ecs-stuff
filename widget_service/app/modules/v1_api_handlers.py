__author__ = 'erik@gettalent'
# Standard Library.
import json
from collections import defaultdict
from uuid import uuid4
# Third Party.
import requests
from flask import jsonify
# Module Specific.
from widget_service.app import db
from widget_service.app import logger
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
    # Initial Setup/Limited validation based on TalentPool and WidgetPage info.
    api_tracker = str(uuid4())
    logger.info('WidgetService::Info  {} - {}'.format(api_tracker, form))

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
    if candidate_single_field_name:
        candidate_dict['full_name'] = candidate_single_field_name
    else:
        candidate_dict['full_name'] = candidate_double_field_name

    candidate_email = form.get('emailAdd')
    if candidate_email:
        candidate_dict['emails'] = [{'address': candidate_email, 'label': 'Primary'}]

    form_aois = form['hidden-tags-aoi']
    if form_aois:
        candidate_dict['areas_of_interest'] = parse_interest_ids_from_form(form_aois, domain_id)

    # Kaiser University Only Field.
    candidate_nuid = form.get('nuid')
    if candidate_nuid:
        nuid_field = db.session.query(CustomField).filter_by(name='NUID', domain_id=domain_id).first()
        if nuid_field:
            candidate_dict.setdefault('custom_fields', []).append({
                'custom_field_id': nuid_field.id,
                'value': candidate_nuid
            })

    # Location based fields.
    candidate_locations = form.get('hidden-tags-location')
    if candidate_locations:
        custom_fields = parse_city_and_state_ids_from_form(candidate_locations, domain_id)
        candidate_dict.setdefault('custom_fields', []).extend(custom_fields)

    candidate_city = form.get('city')
    candidate_state = form.get('state')
    if candidate_city and candidate_state:
        city_state_list = process_city_and_state_from_fields(candidate_city, candidate_state, domain_id)
        candidate_dict.setdefault('custom_fields', []).extend(city_state_list)

    candidate_frequency = form.get('jobFrequency')
    if candidate_frequency:
        frequency_field = db.session.query(CustomField).filter_by(
            name='Subscription Preference', domain_id=domain_id).first()
        candidate_dict.setdefault('custom_fields', []).append({
            'custom_field_id': frequency_field.id,
            'value': candidate_frequency
        })

    # Education fields.
    candidate_graduation_date = form.get('graduation')
    if candidate_graduation_date:
        candidate_graduation_date = candidate_graduation_date.split(' ')[1]

    candidate_dict['educations'] = [{
        'school_name':
        form.get('university'),
        'degrees': [{
            'type': form.get('degree'),
            'title': form.get('major'),
            'end_year': candidate_graduation_date,
        }]
    }]

    # Military specific processing.
    military_service_dict = {
        'branch': form.get('militaryBranch'),
        'status': form.get('militaryStatus'),
        'highest_grade': form.get('militaryGrade'),
        'to_date': form.get('militaryToDate')
    }

    candidate_dict['military_services'] = [military_service_dict]

    candidate_dict['talent_pool_ids']['add'] = [talent_pool.id]
    logger.info("WidgetService::Info - {} - Finished Candidate {}".format(api_tracker, candidate_dict))
    payload = json.dumps({'candidates': [candidate_dict]})

    response = requests.post(
        CandidateApiUrl.CANDIDATES,
        data=payload,
        headers={'Authorization': widget_token,
                 'Content-Type': 'application/json'})

    if response.status_code != 201:
        logger.error("WidgetService::Error::CandidateResponse - {}".format(response.content))
        # Todo return error page
        raise InvalidUsage(error_message='Error creating candidate via Widget')
    # TODO return success template
    return jsonify(candidate_dict), 201

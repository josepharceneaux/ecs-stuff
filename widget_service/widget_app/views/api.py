"""Widget serving/processing"""
__author = 'erikfarmer'

# Standard library
import json

# Framework specific/Third Party
from flask import Blueprint
from flask import current_app as app
from flask import jsonify
from flask import request
from flask import render_template
import requests

# Module specific
from widget_service.common.models.candidate import University
from widget_service.common.models.misc import AreaOfInterest
from widget_service.common.models.misc import Major
from widget_service.common.models.user import Domain
from widget_service.common.models.user import User
from widget_service.common.models.widget import WidgetPage
from widget_service.widget_app import db
from widget_service.widget_app.views.utils import parse_interest_ids_from_form
from widget_service.widget_app.views.utils import parse_city_and_state_ids_from_form

mod = Blueprint('widget_api', __name__)


@mod.route('/test/<domain>', methods=['GET'])
def show_widget(domain):
    """ Route for testing template rendering/js functions/etc.
    :param domain: (string) the domain associated with an html template in for local testing.
    :return: a rendered HTML page.
    """
    if app.config['ENVIRONMENT'] != 'dev':
        return 'Error', 400
    if domain == 'kaiser-military':
        return render_template('kaiser_military.html', domain=domain)
    elif domain == 'kaiser-university':
        return render_template('kaiser_2.html', domain=domain)
    elif domain == 'kaiser-corp':
        return render_template('kaiser_3.html', domain=domain)


@mod.route('/widget/<widget_name>', methods=['GET'])
def process_widget(widget_name):
    """This function will likely not be used as our pages will ideally be stored in S3.
    """
    widget = db.session.query(WidgetPage).filter_by(widget_name=widget_name).first()
    return widget.widget_html, 200


#TODO This should dynamically add 'optiona' field such as preferred location/military experience.
@mod.route('/widget/candidates', methods=['POST'])
def create_candidate_from_widget():
    """ Post receiver for processing widget date.
    :return: A success or error message to change the page state of a widget.
    """
    form = request.form
    candidate_dict = {
        'full_name': '{} {}'.format(form['firstName'], form['lastName']),
        'emails': [{'address': form['emailAdd'], 'label': 'Primary'}],
        'areas_of_interest':  parse_interest_ids_from_form(form['hidden-tags-aoi']),
        'custom_fields': parse_city_and_state_ids_from_form(form['hidden-tags-location'])
    }
    payload = json.dumps({'candidates': [candidate_dict]})
    try:
        request = requests.post(app.config['CANDIDATE_CREATION_URI'], data=payload,
                          headers={'Authorization': app.config['OAUTH_TOKEN'].access_token})
    except:
        return jsonify({'error': {'message': 'unable to create candidate from form'}})
    return jsonify({'success': {'message': 'candidate successfully created'}}), 201


@mod.route('/interests/<domain>', methods=['GET'])
def get_areas_of_interest(domain):
    """ API call that provides interests list filtered by the domain.
    :param domain: (string)
    :return: A dictionary pointing to primary and seconday interests that have been filtered by
             domain.
    """
    current_domain = Domain.query.filter_by(name=domain).first()
    interests = db.session.query(AreaOfInterest).filter(
        AreaOfInterest.domain_id == current_domain.id)
    primary_interests = []
    secondary_interests = []
    for interest in interests:
        if interest.parent_id:
            secondary_interests.append({
                'description': interest.description,
                'parent_id': interest.parent_id
            })
        else:
            primary_interests.append({
                'id': interest.id,
                'description': interest.description,
                'parent_id': interest.parent_id
            })
    return jsonify({'primary_interests': primary_interests,
                    'secondary_interests': secondary_interests})


@mod.route('/universities', methods=['GET'])
def get_university_names():
    """API call for names of universities in db in format used by widget select tags."""
    university_names = db.session.query(University.name)
    # return jsonify(universities_list=[name for name in university_names])
    return jsonify({'universities_list': [university.name for university in university_names]})


@mod.route('/majors/<domain_name>', methods=['GET'])
def get_major_names(domain_name):
    """API call for returning list of major names filtered by domain"""
    domain_id = db.session.query(Domain.id).filter(Domain.name==domain_name)
    majors = db.session.query(Major.name).filter(domain_id==domain_id)
    return jsonify(majors=[major for major in majors])

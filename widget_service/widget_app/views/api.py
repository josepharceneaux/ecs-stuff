"""Widget serving/processing"""
__author = 'erikfarmer'

# Framework specific
from flask import Blueprint
from flask import current_app as app
from flask import jsonify
from flask import request
from flask import render_template

# Module specific
from common.models.misc import AreaOfInterest
from common.models.db import db
from common.models.user import Domain
from common.models.user import User
from common.models.candidate import University
from common.models.widget import WidgetPage


mod = Blueprint('widget_api', __name__)


@mod.route('/test/<domain>', methods=['GET'])
def widget(domain):
    if app.config['ENVIRONMENT'] != 'dev':
        return 'Error', 400
    if domain == 'kaiser-military':
        return render_template('kaiser_military.html', domain=domain)
    elif domain == 'kaiser-university':
        return render_template('kaiser_2.html', domain=domain)
    elif domain == 'kaiser-corp':
        return render_template('kaiser_3.html', domain=domain)


@mod.route('/<widget_name>', methods=['GET', 'POST'])
def process_widget(widget_name):
    if request.method == 'GET':
        return render_widget_via_name(widget_name)


def render_widget_via_name(widget_name):
    widget = WidgetPage.query.filter_by(widget_name=widget_name).first()
    return widget.widget_html, 200


def process_widget_submission(domain):
    return jsonify(domain=domain)


@mod.route('/interests/<widget_name>', methods=['GET'])
def get_areas_of_interest(widget_name):
    current_widget = WidgetPage.query.filter_by(widget_name=widget_name).first()
    widget_user = User.query.get(current_widget.user_id)
    interests = db.session.query(AreaOfInterest).filter(
        AreaOfInterest.domain_id == widget_user.domain_id)
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
                'description': interest.description,
                'parent_id': interest.parent_id
            })
    return jsonify({'primary_interests': primary_interests,
                    'secondary_interests': secondary_interests})


@mod.route('/universities', methods=['GET'])
def get_university_names():
    university_names = db.session.query(University.name)
    return jsonify(universities=[uni for uni in university_names])

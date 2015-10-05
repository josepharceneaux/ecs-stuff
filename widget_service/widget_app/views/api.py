"""Widget serving/processing"""
__author = 'erikfarmer'

# Framework specific
from flask import Blueprint
from flask import jsonify
from flask import request
from flask import render_template

# Module specific
from common.models.misc import AreaOfInterest
from common.models.db import db


mod = Blueprint('widget_api', __name__)


@mod.route('/<domain>', methods=['GET', 'POST'])
def widget(domain):
    if request.method == 'GET':
        if domain == 'kaiser-military':
            return render_template('kaiser_military.html', domain=domain)
        elif domain == 'kaiser-university':
            return render_template('kaiser_2.html', domain=domain)
        elif domain == 'kaiser-corp':
            return render_template('kaiser_3.html', domain=domain)
        else:
            return 'Return error message or awesome 404 page', 404


@mod.route('/interests', methods=['GET'])
def get_areas_of_interest(domain_id):
    interests = db.session.query(AreaOfInterest).filter(AreaOfInterest.domain_id== domain_id)
    primary_interests = []
    secondary_interests = []
    for interest in interests:
        if interest.parent_id:
            secondary_interests.append(interest)
        else:
            primary_interests.append(interest)
    return jsonify({'primary_interests': primary_interests,
                    'secondary_interests': secondary_interests})
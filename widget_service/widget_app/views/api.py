"""Widget serving/processing"""
__author = 'erikfarmer'

from flask import Blueprint
from flask import request
from flask import render_template


mod = Blueprint('widget_api', __name__)


@mod.route('/<domain>', methods=['GET', 'POST'])
def widget(domain):
    if request.method == 'GET':
        if domain == 'kaiser-military':
            return render_template('kaiser_military.html', domain=domain)
        else:
            return 'Return error message or awesome 404 page', 404
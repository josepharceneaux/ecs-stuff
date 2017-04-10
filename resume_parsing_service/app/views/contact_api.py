from flask import Blueprint
from flask.ext.cors import CORS

CONTACT_MOD = Blueprint('contact_only', __name__)

CORS(
    CONTACT_MOD,
    resources={
        r'/v1/contact_only': {
            'origins': [r"*.gettalent.com", "http://localhost"],
            'allow_headers': ['Content-Type', 'Authorization']
        }
    })


@CONTACT_MOD.route('/contact_only', methods=['POST'])
def get_contact_info():
    return "Hi there"
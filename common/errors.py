__author__ = 'amirhb'
from flask import jsonify

# Todo: import response
def forbidden(message):
    response = jsonify({'error': {'code': 100, 'message': message}})
    response.status_code = 403
    return response

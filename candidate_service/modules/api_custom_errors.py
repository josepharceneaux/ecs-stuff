__author__ = 'amirhb'
from flask import jsonify


def bad_request_error(message):
    response = jsonify({'error': {'message': message}})
    response.status_code = 400
    return response


def unauthorized_error(message='Authentication failed'):
    response = jsonify({'error': {'message': message}})
    response.status_code = 401
    return response


def forbidden_error(message='Not authorized'):
    response = jsonify({'error': {'message': message}})
    response.status_code = 403
    return response


def not_found_error(message='Page not found'):
    response = jsonify({'error': {'message': message}})
    response.status_code = 404
    return response





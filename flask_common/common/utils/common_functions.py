import re
import json
import requests
import random
import string
from werkzeug.security import generate_password_hash
from ..models.user import User, UserScopedRoles

OAUTH_ENDPOINT = 'http://127.0.0.1:8001/%s'
TOKEN_URL = OAUTH_ENDPOINT % 'oauth2/token'

from ..error_handling import ForbiddenError
from sqlalchemy.sql.expression import ClauseElement


def get_or_create(session, model, defaults=None, **kwargs):
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance, False
    else:
        params = dict((k, v) for k, v in kwargs.iteritems() if not isinstance(v, ClauseElement))
        params.update(defaults or {})
        instance = model(**params)
        session.add(instance)
        return instance, True


def get_geocoordinates(location):
    url = 'http://maps.google.com/maps/api/geocode/json'
    r = requests.get(url, params=dict(address=location, sensor='false'))
    try:
        geodata = r.json()
    except:
        geodata = r.json

    results = geodata.get('results')
    if results:
        location = results[0].get('geometry', {}).get('location', {})

        lat = location.get('lat')
        lng = location.get('lng')
    else:
        lat, lng = None, None

    return lat, lng


def get_coordinates(zipcode=None, city=None, state=None, address_line_1=None, location=None):
    """
    Function gets the coordinates of a location using Google Maps
    :param location: if provided, overrides all other inputs
    :return: string of "lat,lon" in degrees, or None if nothing found
    """
    coordinates = None

    location = location or "%s%s%s%s" % (
        address_line_1 + ", " if address_line_1 else "",
        city + ", " if city else "",
        state + ", " if state else "",
        zipcode or ""
    )
    latitude, longitude = get_geocoordinates(location)
    if latitude and longitude:
        coordinates = "%s,%s" % (latitude, longitude)

    return coordinates


# TODO: Remove prints
def http_request(method_type, url, params=None, headers=None, data=None, user_id=None):
    """
    This is common function to make HTTP Requests. It takes method_type (GET or POST)
    and makes call on given URL. It also handles/logs exception.
    :param method_type: GET or POST.
    :param url: resource URL.
    :param params: params to be sent in URL.
    :param headers: headers for Authorization.
    :param data: data to be sent.
    :param user_id: Id of logged in user.
    :return: response from HTTP request or None
    """
    response = None
    if method_type in ['GET', 'POST', 'PUT', 'DELETE']:
        method = getattr(requests, method_type.lower())
        error_message = None
        if url:
            try:
                response = method(url, params=params, headers=headers, data=data, verify=False)
                # If we made a bad request (a 4XX client error or 5XX server
                # error response),
                # we can raise it with Response.raise_for_status():"""
                response.raise_for_status()
            except requests.exceptions.HTTPError as e:
                if e.response.status_code in [401]:
                    # 401 is the error code for Not Authorized user(Expired Token)
                    raise
                # checks if error occurred on "Server" or is it a bad request
                elif e.response.status_code < 500:
                    try:
                        if 'errors' in e.response.json():
                            error_message = e.message + ', Details: ' \
                                            + json.dumps(
                                e.response.json().get('errors'))
                        elif 'error_description' in e.response.json():
                            error_message = e.message + ', Details: ' \
                                            + json.dumps(
                                e.response.json().get('error_description'))
                        else:
                            error_message = e.message
                    except:
                        error_message = e.message
                else:
                    # raise any Server error
                    raise
            except requests.RequestException as e:
                if hasattr(e.message, 'args'):
                    if 'Connection aborted' in e.message.args[0]:
                        print "Couldn't make %s call on %s. Make sure " \
                              "requested server is running." % (method_type, url)
                        raise ForbiddenError
                error_message = e.message
            if error_message:
                print 'http_request: HTTP request failed, %s, user_id: %s', error_message, user_id
            return response
        else:
            error_message = 'URL is None. Unable to make "%s" Call' % method_type
            print 'http_request: Error: %s, user_id: %s' % (error_message, user_id)
    else:
        print 'Unknown Method type %s ' % method_type


def find_missing_items(data_dict, required_fields=None, verify_all_keys=False):
    """
    This function is used to find the missing items in given data_dict. If verify_all
    is true, this function checks all the keys present in data_dict if they are empty or not.
    Otherwise it verify only those fields as given in required_fields.

    :param data_dict: given dictionary to be examined
    :param required_fields: keys which need to be checked
    :param verify_all_keys: indicator if we want to check values of all keys or only keys
                            present in required_fields
    :type data_dict: dict
    :type required_fields: list | None
    :type verify_all_keys: bool
    :return: list of missing items
    :rtype: list
    """
    if verify_all_keys:
        missing_items = [{key: value} for key, value in data_dict.iteritems()
                         if not value and not value == 0]
    else:
        missing_items = [{key: value} for key, value in data_dict.iteritems()
                         if key in required_fields and not value and not value == 0]
    return [missing_item for missing_item in missing_items]


def create_test_user(session, domain_id, password):
    random_email = ''.join([random.choice(string.ascii_letters + string.digits) for n in xrange(12)])
    email = '%s.sample@example.com' % random_email
    first_name = 'John'
    last_name = 'Sample'
    test_user = User(
        email=email,
        password=generate_password_hash(password, method='pbkdf2:sha512'),
        domain_id=domain_id,
        first_name=first_name,
        last_name=last_name,
        expiration=None
    )
    session.add(test_user)
    session.commit()
    return test_user


def get_access_token(user, password, client_id, client_secret):
    params = dict(grant_type="password", username=user.email, password=password)
    auth_service_token_response = requests.post(TOKEN_URL,
                                                params=params, auth=(client_id, client_secret)).json()
    if not (auth_service_token_response.get(u'access_token') and auth_service_token_response.get(u'refresh_token')):
        raise Exception("Either Access Token or Refresh Token is missing")
    else:
        return auth_service_token_response.get(u'access_token')


def add_role_to_test_user(test_user, role_names):
    """
    This function will add roles to a test_user just for testing purpose
    :param User test_user: User object
    :param list[str] role_names: List of role names
    :return:
    """
    UserScopedRoles.add_roles(test_user, role_names)


def camel_case_to_snake_case(name):
    """ Convert camel case to underscore case
        socialNetworkId --> social_network_id

            :Example:

                result = camel_case_to_snake_case('socialNetworkId')
                assert result == 'social_network_id'

    """
    # name_ = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    # return re.sub('([a-z0-9])([A-Z0-9])', r'\1_\2', name_).lower()
    name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    name = re.sub('(.)([0-9]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()
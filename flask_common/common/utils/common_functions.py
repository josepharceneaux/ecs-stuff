import json
from sqlalchemy.sql.expression import ClauseElement
import requests


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
                response = method(url, params=params, headers=headers, data=data)
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
                else:
                    # raise any Server error occurred on social network website
                    raise
            except requests.RequestException as e:
                error_message = e.message
            if error_message:
                print 'http_request: HTTP request failed, %s, user_id: %s', error_message, user_id
            return response
        else:
            error_message = 'URL is None. Unable to make "%s" Call' % method_type
            print 'http_request: Error: %s, user_id: %s' % (error_message, user_id)
    else:
        print 'Unknown Method type %s ' % method_type


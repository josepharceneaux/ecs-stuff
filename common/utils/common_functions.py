from sqlalchemy.sql.expression import ClauseElement
from activity_service.common.models.db import db
from activity_service.activities_app import app
from flask import current_app
import requests


# Setting current app context
with app.app_context():
    db.session.commit()
    print "current running app: %s" % current_app.name


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
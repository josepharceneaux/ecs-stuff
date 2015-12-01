"""
This file is for all geo related functions
"""
from geo_location import GeoLocation
import requests


def get_geo_coordinates(location):
    """Google location (lat/lon) service.
    :param location
    """
    url = 'http://maps.google.com/maps/api/geocode/json'
    r = requests.get(url, params=dict(address=location, sensor='false'))
    try:
        geo_data = r.json()
    except Exception:
        geo_data = r.json

    results = geo_data.get('results')
    if results:
        location = results[0].get('geometry', {}).get('location', {})

        lat = location.get('lat')
        lng = location.get('lng')
    else:
        lat, lng = None, None

    return lat, lng


def get_coordinates(zipcode=None, city=None, state=None, address_line_1=None, location=None):
    """

    :param location: if provided, overrides all other inputs
    :param city
    :param state
    :param zipcode
    :param address_line_1
    :return: string of "lat,lon" in degrees, or None if nothing found
    """
    coordinates = None

    location = location or "%s%s%s%s" % (
        address_line_1 + ", " if address_line_1 else "",
        city + ", " if city else "",
        state + ", " if state else "",
        zipcode or ""
    )
    latitude, longitude = get_geo_coordinates(location)
    if latitude and longitude:
        coordinates = "%s,%s" % (latitude, longitude)

    return coordinates


def get_geo_coordinates_bounding(address, distance):
    """
    Using google maps api get coordinates, get coordinates, and bounding box with top left and bottom right coordinates
    :param address
    :param distance
    :return: coordinates and bounding box coordinates
    """
    lat, lng = get_geo_coordinates(address)
    if lat and lng:
        # get bounding box based on location coordinates and distance given
        loc = GeoLocation.from_degrees(lat, lng)
        sw_loc, ne_loc = loc.bounding_locations(distance)
        # cloud search requires top left and bottom right coordinates
        north_west = ne_loc.deg_lat, sw_loc.deg_lon
        south_east = sw_loc.deg_lat, ne_loc.deg_lon
        return {'top_left':north_west, 'bottom_right': south_east, 'point':(lat, lng)}
    return False

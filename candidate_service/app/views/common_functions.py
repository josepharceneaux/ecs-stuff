__author__ = 'naveen'


def users_in_domain(domain_id):
        """Returns all the users for provided domain id, Uses cache
        params: domain_id: Domain id
        returns: database users in given domain
        """
        from candidate_service.common.models.db import get_table
        users = get_table("user")
        user_domain = users.select(users.c.domainId == domain_id).execute().first()
        return user_domain


def get_geo_coordinates(location):
    """Google location (lat/lon) service."""
    import requests
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


def get_geo_coordinates_bounding(address, distance):
    """
    Using google maps api get coordinates, get coordinates, and bounding box with top left and bottom right coordinates
    :return: coordinates and bounding box coordinates
    """
    from geo_location import GeoLocation
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

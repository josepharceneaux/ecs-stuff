import requests


def get_geocoordinates(location):
    url = 'http://maps.google.com/maps/api/geocode/json'
    r = requests.get(url, params=dict(address=location, sensor='false'))
    try:
        geodata = r.json()
    except:
        geodata = r.json

    results = geodata.get('results')
    if len(results):
        location = results[0].get('geometry', {}).get('location', {})

        lat = location.get('lat')
        lng = location.get('lng')
    else:
        lat, lng = None, None

    return lat, lng


def get_geo_coordinates_bounding(address, distance):
    """
    Using google maps api get coordinates, get coordinates, and bounding box with top left and bottom right coordinates
    :param location: takes address/ city / zip code as location
    :return: coordinates and bounding box coordinates
    """
    from geo_location import GeoLocation
    lat, lng = get_geocoordinates(address)
    if lat and lng:
        # get bounding box based on location coordinates and distance given
        loc = GeoLocation.from_degrees(lat, lng)
        SW_loc, NE_loc = loc.bounding_locations(distance)
        # cloudsearch requires top left and bottom right coordinates
        north_west = NE_loc.deg_lat, SW_loc.deg_lon
        south_east = SW_loc.deg_lat, NE_loc.deg_lon
        return {'top_left':north_west, 'bottom_right':south_east, 'point':(lat, lng)}
    return False
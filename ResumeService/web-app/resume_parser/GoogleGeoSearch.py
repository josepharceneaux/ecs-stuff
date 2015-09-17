import requests


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

__author__ = 'naveen'

from candidate_service.common.models.db import get_table, conn_db
from sqlalchemy import select
import requests


def users_in_domain(domain_id):
        """
        Returns all the users for provided domain id
        Uses cache
        params:
            domain_id: Domain id
        returns;
            database users in given domain

        :rtype: gluon.dal.objects.Rows
        """
        users = get_table("user")
        user_domain = users.select(users.c.domainId == domain_id).execute().first()
        return user_domain


# Gets or creates AOIs
def get_or_create_areas_of_interest(domain_id, include_child_aois=False):

    default_area_of_interests = ['Production & Development', 'Marketing', 'Sales', 'Design', 'Finance',
                                 'Business & Legal Affairs', 'Human Resources', 'Technology', 'Other']
    if not domain_id:
        pass
        # current.logger.error("get_or_create_areas_of_interest: domain_id is %s!", domain_id)
    aois = get_table('area_of_interest')
    stmt = select([aois.c.id]).where(aois.c.domainId == domain_id).order_by(aois.c.id.asc())
    areas = conn_db.execute(stmt).fetchall()

    # areas = db(db.area_of_interest.domainId == domain_id).select(orderby=db.area_of_interest.id)

    # If no AOIs exist, create them
    if not len(areas):
        for description in default_area_of_interests:
            aois = get_table('area_of_interest')
            stmt = aois.insert().values(description=description, domainId=domain_id)
            ins = conn_db.execute(stmt)
            # db.area_of_interest.insert(description=description, domainId=domain_id)
        stmt = select([aois.c.id]).where(aois.c.domainId == domain_id).order_by(aois.c.id.asc())
        areas = conn_db.execute(stmt).fetchall()
        # areas = db(db.area_of_interest.domainId == domain_id).select(orderby=db.area_of_interest.id)

    # If we only want parent AOIs, must filter for all AOIs that don't have parentIds
    if not include_child_aois:
        areas = areas.find(lambda aoi: not aoi.parentId)

    return areas


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
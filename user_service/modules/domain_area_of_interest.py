"""
Helper functions for domain area(s) of interest CRUD operations
Note: "AOI" or "aoi" refers to "area of interest"
"""
from user_service.user_app import logger
from user_service.common.models.db import db
from user_service.common.models.user import User
from user_service.common.models.misc import AreaOfInterest
from user_service.common.error_handling import InvalidUsage, NotFoundError, ForbiddenError


def create_or_update_domain_aois(domain_id, aois, aoi_id_from_url=None, is_creating=False, is_updating=False):
    """
    Function will create or update domain AOI(s).
    Function must not be used to create AND update in the same call.

    AOI description is a required field

    Create Caveats:
        - AOI must not exists in db for a successful creation
    Update Caveats:
        - AOI ID must be provided for updating
        - If aoi_id_from_url is provided, only one record may be updated
        _ AOI must belong to user's domain

    :type domain_id:  User
    :param domain_id: logged in user's domain ID
    :type aois:  list[dict]
    :param aois: a list of dicts containing area of interest's information
    :type aoi_id_from_url: basestring
    :param aoi_id_from_url: area of interest's ID provided in resource's url
    :type is_creating: bool
    :type is_updating: bool
    :rtype:  list[int]
    """
    created_or_updated_aoi_ids = []  # Aggregate created or updated aoi ids here
    for aoi in aois:
        aoi_id = aoi.get('id')

        # normalize AOI's description
        aoi_description = aoi['description'].lower().strip()
        if not aoi_description:  # In case description is just a whitespace
            logger.error("Description not provided for area of interest. Description = %s", aoi_description)
            raise InvalidUsage("Description is required for creating/updating area of interest.")

        if is_creating:  # create
            # Prevent duplicate entries for the same domain
            aoi_object = AreaOfInterest.query.filter_by(domain_id=domain_id, name=aoi_description).first()
            if aoi_object:
                raise InvalidUsage("Creation failed: Area of interest already exists",
                                   additional_error_info=dict(id=aoi_object.id))
            else:
                aoi_object = AreaOfInterest(domain_id=domain_id, name=aoi_description)
                db.session.add(aoi_object)
                db.session.flush()
                created_or_updated_aoi_ids.append(aoi_object.id)

        elif is_updating:  # update
            aoi_id = aoi_id or aoi_id_from_url
            if not aoi_id:
                raise InvalidUsage("Area of interest ID is required for updating")

            # Area of interest must be recognized
            aoi_object = AreaOfInterest.get(aoi_id)
            if not aoi_object:
                logger.error('Area of interest ID not recognized. ID = %s', aoi_id)
                raise NotFoundError("Area of interest ID not recognized. ID = %s" % aoi_id)

            # Area of interest must belong to user's domain
            if aoi_object.domain_id != domain_id:
                raise ForbiddenError("Not authorized")

            aoi_object.update(name=aoi_description)
            created_or_updated_aoi_ids.append(aoi_id)

    db.session.commit()
    return created_or_updated_aoi_ids


def retrieve_domain_aoi(domain_id, aoi_id):
    """
    Function will retrieve aoi from db
    Caveats:
        1. AOI ID must be recognized
        2. AOI must belong to the specified domain
    :type domain_id:  int | long
    :type aoi_id:     int | long
    """
    # Area of interest id must be recognized
    aoi_object = AreaOfInterest.get(aoi_id)
    if not aoi_object:
        logger.error('Area of interest ID not recognized. ID = %s', aoi_id)
        raise NotFoundError("Area of interest ID not recognized. ID = %s" % aoi_id)

    # Area of interest must belong to user's domain
    if aoi_object.domain_id != domain_id:
        logger.error('Unauthorized access. aoi_domain_id = %s,\tuser_domain_id = %s', aoi_object.domain_id, domain_id)
        raise ForbiddenError("Not authorized")

    return {
        "id": aoi_object.id,
        "domain_id": aoi_object.domain_id,
        "description": aoi_object.name
    }


def delete_domain_aoi(domain_id, aoi_id):
    """
    :type domain_id:  int | long
    :type aoi:        int | long
    :rtype:           int | long
    """
    aoi_object = AreaOfInterest.get(aoi_id)

    # Area of interest ID must be recognized
    if not aoi_object:
        logger.error('Area of interest ID not recognized. ID = %s', aoi_id)
        raise NotFoundError("Area of interest ID not recognized. ID = %s" % aoi_id)

    # Area of interest must belong to user's domain
    if aoi_object.domain_id != domain_id:
        logger.error('Unauthorized access. aoi_domain_id = %s,\tuser_domain_id = %s', aoi_object.domain_id, domain_id)
        raise ForbiddenError("Not authorized")

    db.session.delete(aoi_object)
    db.session.commit()
    return


def delete_domain_aois(domain_id):
    """
    Function will delete all of domain's areas of interest
    :type domain_id: int | long
    :rtype:  list(int)
    """
    domain_aois = AreaOfInterest.get_domain_areas_of_interest(domain_id)
    deleted_aoi_ids = [aoi.id for aoi in domain_aois]
    if not domain_aois:
        raise InvalidUsage("Domain has no area of interest")

    map(db.session.delete, domain_aois)
    db.session.commit()
    return deleted_aoi_ids

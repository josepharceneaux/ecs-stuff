"""
This file contains functions for candidate tag(s) CRUD operations
"""
# Models
from candidate_service.common.error_handling import NotFoundError, ForbiddenError, InvalidUsage
from candidate_service.common.models.db import db
from candidate_service.common.models.tag import Tag, CandidateTag
from candidate_service.custom_error_codes import CandidateCustomErrors as custom_error


def create_tags(candidate_id, tags):
    """
    :type candidate_id: int|long
    :type tags:         list[dict]
    :rtype:             list[int]
    """
    created_tag_ids = []
    for tag in tags:
        # Prevent adding duplicate tags to db
        tag_name = tag['name']
        tag_object = Tag.query.filter_by(name=tag_name).first()
        if not tag_object:
            tag_object = Tag(name=tag_name)
            db.session.add(tag_object)
            db.session.flush()

        tag_id = tag_object.id

        # Insert into CandidateTag table
        candidate_tag_object = CandidateTag.get_by(candidate_id=candidate_id, tag_id=tag_id)
        if not candidate_tag_object:
            db.session.add(CandidateTag(candidate_id=candidate_id, tag_id=tag_id))
            db.session.commit()
            created_tag_ids.append(tag_id)

    return created_tag_ids


def get_tags(candidate_id, tag_id=None):
    """
    :type candidate_id:  int|long
    :type tag_id:        int|long
    :return:
    """
    # Return specified tag if tag_id is provided
    if tag_id:
        tag_object = Tag.get(tag_id)
        if not tag_object:
            raise NotFoundError('Tag ID ({}) is not recognized.'.format(tag_id), custom_error.TAG_NOT_FOUND)

        # Tag must belong to candidate
        if not CandidateTag.query.filter_by(tag_id=tag_id, candidate_id=candidate_id).first():
            raise ForbiddenError('Tag (id = {}) does not belong to candidate (id = {})'.format(tag_id, candidate_id),
                                 custom_error.TAG_FORBIDDEN)

        return {'name': tag_object.name}

    # Return all of candidate's tags if tag_id is not provided
    candidate_tags = CandidateTag.get_all(candidate_id)
    if not candidate_tags:
        raise NotFoundError('Candidate is not associated with any tags', custom_error.TAG_NOT_FOUND)

    tags = []
    for candidate_tag in candidate_tags:
        tag = Tag.get(candidate_tag.tag_id)
        tags.append(dict(id=tag.id, name=tag.name))

    return {'tags': tags}


def update_candidate_tag(candidate_id, tag_id, tag_name):
    """
    Function will update candidate's tag
    :type candidate_id: int | long
    :type tag_id:       int | long
    :type tag_name      str
    :param tag_name     name of the tag, e.g. 'diligent', 'minority'
    :rtype  dict[int|long]
    """
    tag_obj_from_id = Tag.get(tag_id)
    if not tag_obj_from_id:
        raise NotFoundError("Tag ID: {} is not recognized".format(tag_id), custom_error.TAG_NOT_FOUND)

    # Candidate must already be associated with provided tag_id
    candidate_tag_query = CandidateTag.query.filter_by(candidate_id=candidate_id, tag_id=tag_id)
    candidate_tag_object = candidate_tag_query.first()
    if not candidate_tag_object:
        raise InvalidUsage('Candidate (id = {}) is not associated with Tag (id = {})'.format(candidate_id, tag_id),
                           custom_error.INVALID_USAGE)

    # If Tag is not found, create it
    tag_object = Tag.get_by_name(tag_name)
    if not tag_object:
        tag_object = Tag(name=tag_name)
        db.session.add(tag_object)
        db.session.flush()

    # Update
    candidate_tag_query.update(dict(candidate_id=candidate_id, tag_id=tag_object.id))
    db.session.commit()
    return {'id': tag_object.id}


def update_candidate_tags(candidate_id, tags):
    """
    Function will update candidate's tag(s)
    :type candidate_id:  int | long
    :type tags:          list[dict]
    :rtype: list[int|long]
    """
    created_tag_ids, updated_tag_ids = [], []
    for tag in tags:
        tag_name, tag_id = tag['name'], tag.get('id')
        tag_object = Tag.get_by_name(tag_name)

        # If Tag is not found, create it
        if not tag_object:
            tag_object = Tag(name=tag_name)
            db.session.add(tag_object)
            db.session.flush()

        # Data for updating candidate's tag
        update_dict = dict(candidate_id=candidate_id, tag_id=tag_object.id)

        if not tag_id:
            raise InvalidUsage('Tag ID is required for updating', custom_error.INVALID_USAGE)

        tag_obj_from_id = Tag.get(tag_id)
        if not tag_obj_from_id:
            raise NotFoundError("Tag ID: {} is not recognized".format(tag_id), custom_error.TAG_NOT_FOUND)

        # Candidate must already be associated with provided tag_id
        candidate_tag_query = CandidateTag.query.filter_by(candidate_id=candidate_id, tag_id=tag_id)
        if not candidate_tag_query.first():
            raise InvalidUsage('Candidate (id = {}) is not associated with Tag (id = {})'.format(candidate_id, tag_id),
                               custom_error.INVALID_USAGE)
        # Update
        candidate_tag_query.update(update_dict)
        updated_tag_ids.append(tag_object.id)

    db.session.commit()
    return updated_tag_ids


def delete_tag(candidate_id, tag_id):
    """
    Function will delete candidate's tag
    :type candidate_id: int | long
    :type tag_id:       int | long
    :rtype  dict
    """
    candidate_tag_object = CandidateTag.get_one(candidate_id, tag_id)
    if not candidate_tag_object:
        raise NotFoundError('Candidate (id = {}) is not associated with tag: {}'.format(candidate_id, tag_id),
                            custom_error.INVALID_USAGE)

    db.session.delete(candidate_tag_object)
    db.session.commit()

    return {'id': tag_id}


def delete_tags(candidate_id):
    """
    Function will delete all of candidate's tags
    :type candidate_id:  int | long
    :rtype  list[dict]
    """
    deleted_tag_ids = []
    for candidate_tag in CandidateTag.get_all(candidate_id):
        deleted_tag_ids.append(candidate_tag.tag_id)
        db.session.delete(candidate_tag)

    db.session.commit()
    return [{'id': tag_id} for tag_id in deleted_tag_ids]

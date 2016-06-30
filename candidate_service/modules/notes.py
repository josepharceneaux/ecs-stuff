"""
Helper functions for candidate's notes CRUD operations
"""
from datetime import datetime
from candidate_service.common.models.db import db
from candidate_service.common.models.candidate import Candidate, CandidateTextComment
from candidate_service.common.utils.handy_functions import normalize_value
from candidate_service.common.error_handling import InvalidUsage, NotFoundError, ForbiddenError
from candidate_service.custom_error_codes import CandidateCustomErrors as custom_error


def add_notes(candidate_id, data):
    """
    Function will insert candidate notes into the db and return their IDs
    Notes must have a comment.
    :type candidate_id:  int|long
    :type data:  list[dict]
    :rtype:  list[int]
    """
    created_note_ids = []

    for note in data:

        # Normalize value
        title = normalize_value(note.get('title')) if note.get('title') else None
        comments = normalize_value(note.get('comment'))

        # Notes must have a comment
        if not comments:
            raise InvalidUsage('Note must have a comment', custom_error.INVALID_USAGE)

        notes_dict = dict(
            candidate_id=candidate_id,
            title=title,
            comment=comments,
            added_time=datetime.utcnow()
        )

        notes_dict = dict((k, v) for k, v in notes_dict.iteritems() if v is not None)
        note_obj = CandidateTextComment(**notes_dict)
        db.session.add(note_obj)
        db.session.flush()
        created_note_ids.append(note_obj.id)

    db.session.commit()
    return created_note_ids


def get_notes(candidate, note_id=None):
    """
    Function will return all of candidate's notes if note_id is not provided, otherwise it
    will return a single note object.
    :type candidate:  Candidate
    :type note_id:  int | long | None
    :rtype: dict | list[dict]
    """
    candidate_id = candidate.id

    # return specified note
    if note_id:

        note = CandidateTextComment.get(note_id)

        # Note ID must be recognized
        if not note:
            raise NotFoundError('Note ID ({}) not recognized'.format(note_id), custom_error.NOTE_NOT_FOUND)

        # Note must belong to the candidate
        if note.candidate_id != candidate_id:
            raise ForbiddenError('Note (id = {}) does not belong to candidate (id = {})'.format(note_id, candidate_id),
                                 custom_error.NOTE_FORBIDDEN)

        return {
            'candidate_note': {
                'id': note_id,
                'candidate_id': candidate_id,
                'owner_id': candidate.user.id,
                'title': note.title,
                'comment': note.comment,
                'added_time': str(note.added_time)
            }
        }

    # return all of candidate's notes
    else:
        # Note's owner ID
        owner_id = candidate.user.id

        candidate_notes = []
        for note in CandidateTextComment.get_by_candidate_id(candidate_id):
            candidate_notes.append({
                'id': note.id,
                'candidate_id': candidate_id,
                'owner_id': owner_id,
                'title': note.title,
                'comment': note.comment,
                'added_time': str(note.added_time)
            })

        return {'candidate_notes': candidate_notes}


def delete_note(candidate_id, note_id):
    """
    Function will delete candidate note.
    Note ID must be recognized & must belong to candidate
    :type candidate_id:  int | long
    :type note_id:  int | long
    """
    note = CandidateTextComment.get(note_id)

    # Note ID must be recognized
    if not note:
        raise NotFoundError('Note ID ({}) not recognized'.format(note_id), custom_error.NOTE_NOT_FOUND)

    # Note must belong to the candidate
    if note.candidate_id != candidate_id:
        raise ForbiddenError('Note (id = {}) does not belong to candidate (id = {})'.format(note_id, candidate_id),
                             custom_error.NOTE_FORBIDDEN)

    db.session.delete(note)
    db.session.commit()
    return note_id


def delete_notes(candidate):
    """
    Function will delete all of candidates notes
    :type candidate:  Candidate
    """
    deleted_note_ids = []
    for note in candidate.text_comments:
        deleted_note_ids.append(note.id)
        db.session.delete(note)

    db.session.commit()
    return {'candidate_notes': [{'id': note_id} for note_id in deleted_note_ids]}

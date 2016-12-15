"""
This migration script will move data from "is_web_hidden" column to "is_archived" column.

Note: As of 12/14/16 "is_web_hidden" is a deprecated field.
"""
from candidate_service.candidate_app import app
from time import time
from candidate_service.common.models.db import db
from candidate_service.common.models.candidate import Candidate
from candidate_service.modules.talent_cloud_search import upload_all_candidate_documents


def migrate_is_web_hidden_data_to_is_archived():
    """
    Function will retrieve all candidates from db and it will:
    1.
      - set candidate's is_archived to 1 if candidate's is_web_hidden had been set to 1, or
      - set candidate's is_archived to 0 if candidate's is_web_hidden had not been set or had been set to 0
    """
    total_number_of_candidates = Candidate.query.count()
    print "total_number_of_candidates: {}".format(total_number_of_candidates)

    start = 0
    batch = 1
    while start < total_number_of_candidates:
        candidates = Candidate.query.slice(start=start, stop=start + 100).all()
        for candidate in candidates:
            if candidate.is_web_hidden == 1:
                candidate.is_archived = 1
            else:
                candidate.is_archived = 0

        db.session.commit()
        print "Batch {} updated candidate IDs: {}".format(batch, [candidate.id for candidate in candidates])
        start += 100
        batch += 1


if __name__ == '__main__':
    try:
        t = time()
        print "starting migrate_is_web_hidden_data_to_is_archived"
        migrate_is_web_hidden_data_to_is_archived()
        print "migration script completed successfully. Time: {}".format(time() - t)

        # Upload all candidate documents
        upload_all_candidate_documents()
    except Exception as e:
        print "Error: {}".format(e.message)

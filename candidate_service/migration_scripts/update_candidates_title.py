"""
This script will set candidate's titles to their most recent job title if candidate has any experience data.
All candidate docs will be uploaded to Cloud Search after update_candidate_title completes successfully
"""
from candidate_service.candidate_app import app
import time
from candidate_service.common.models.db import db
from candidate_service.common.models.candidate import Candidate, CandidateExperience
from candidate_service.modules.talent_cloud_search import upload_all_candidate_documents


def update_candidates_title():
    """
    Function will set candidate's most recent experience's position as its new title, if candidate's title is
    empty and candidate has at least one experience data
    """
    start, batch = 0, 1
    candidates_count = Candidate.query.count()
    print "total number of candidates: {}".format(candidates_count)

    # To prevent heavy transaction load on DB, execute in batched of maximum 50
    while start < candidates_count:
        candidates_with_no_title = Candidate.query. \
            filter((Candidate.title == None) | (Candidate.title == '')). \
            slice(start=start, stop=start + 50).all()

        print "number of candidates processing: {}".format(len(candidates_with_no_title))

        for candidate in candidates_with_no_title:

            # Retrieve candidate's most recent work experience
            most_recent_experience = CandidateExperience.query.filter_by(candidate_id=candidate.id). \
                order_by(CandidateExperience.is_current.desc(),
                         CandidateExperience.end_year.desc(),
                         CandidateExperience.start_year.desc(),
                         CandidateExperience.end_month.desc(),
                         CandidateExperience.start_month.desc()).first()  # type: CandidateExperience

            if most_recent_experience:
                new_title = most_recent_experience.position
                print "candidate: {id}\nnew_title: {title}".format(id=candidate.id, title=new_title)
                candidate.title = new_title

            start += 50
            batch += 1

        db.session.commit()


if __name__ == '__main__':
    try:
        start_time = time.time()
        update_candidates_title()

        # Upload all candidate documents to Cloud Search
        upload_all_candidate_documents()
        print "update_candidates_title successful. Time: {}".format(time.time() - start_time)
    except Exception as e:
        db.session.rollback()
        print "Error: {}".format(e.message)

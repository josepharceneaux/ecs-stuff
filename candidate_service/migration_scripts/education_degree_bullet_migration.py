"""
This migration script will move the concentration_type and comment column data from "candidate_education_degree_bullet"
to the newly-created fields in "candidate_education_degree"
"""
from candidate_service.candidate_app import app
from time import time
from candidate_service.common.models.db import db
from candidate_service.common.models.candidate import Candidate
from candidate_service.common.models.candidate import CandidateEducation
from candidate_service.common.models.candidate import CandidateEducationDegree
from candidate_service.common.models.candidate import CandidateEducationDegreeBullet


def migrate_bullet_data_to_education_degree():

    total_number_of_candidates = Candidate.query.count()
    print "total_number_of_candidates: {}".format(total_number_of_candidates)
    
    start = 0
    batch = 1
    while start < total_number_of_candidates:
        candidates = Candidate.query.slice(start=start, stop=start + 100)
        for candidate in candidates:
            can_edu = CandidateEducation.query.filter_by(candidate_id=candidate.id).all()
            for education in can_edu:
                can_edu_deg = CandidateEducationDegree.query.filter_by(candidate_education_id=education.id).all()
                for degree in can_edu_deg:
                    # We only want the first bullet -- other bullets will be discarded
                    can_edu_deg_bul = CandidateEducationDegreeBullet.query.filter_by(candidate_education_degree_id=degree.id).first()
                    if can_edu_deg_bul:
                        # Merge over concentration_type
                        if can_edu_deg_bul.concentration_type:
                            degree.concentration_type = can_edu_deg_bul.concentration_type
                        # Merge over comments
                        if can_edu_deg_bul.comments:
                            degree.comments = can_edu_deg_bul.comments

        db.session.commit()
        print "Batch {} updated candidate IDs: {}".format(batch, [candidate.id for candidate in candidates])
        start += 100
        batch += 1

if __name__ == '__main__':
    try:
        t = time()
        print "starting migrate_bullet_data_to_education_degree"
        migrate_bullet_data_to_education_degree()
        print "migration script completed successfully. Time: {}".format(time() - t)

    except Exception as e:
        print "Error: {}".format(e.message)

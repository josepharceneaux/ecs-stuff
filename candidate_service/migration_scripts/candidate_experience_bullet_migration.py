"""
This migration script will move "description" column data from "candidate_experience_bullet" table (table will later be removed)
to a newly-created description field in "candidate_experience"
"""
from candidate_service.candidate_app import app
from time import time
from candidate_service.common.models.db import db
from candidate_service.common.models.candidate import Candidate
from candidate_service.common.models.candidate import CandidateExperience
from candidate_service.common.models.candidate import CandidateExperienceBullet


def migrate_description_from_bullet_to_candidate_experience():

    total_number_of_candidates = Candidate.query.count()
    print "total_number_of_candidates: {}".format(total_number_of_candidates)
    
    start = 0
    batch = 1
    while start < total_number_of_candidates:
        candidates = Candidate.query.slice(start=start, stop=start + 100)
        for candidate in candidates:
            # Migrate the work experience bullets
            can_exp = CandidateExperience.query.filter_by(candidate_id=candidate.id).all()
            for experience in can_exp:
                # We only want the first bullet -- other bullets will be discarded
                can_exp_bullet = CandidateExperienceBullet.query.filter_by(candidate_experience_id=experience.id).first()
                if can_exp_bullet and can_exp_bullet.description:
                    experience.description = can_exp_bullet.description

        db.session.commit()
        print "Batch {} updated candidate IDs: {}".format(batch, [candidate.id for candidate in candidates])
        start += 100
        batch += 1

if __name__ == '__main__':
    try:
        t = time()
        print "starting migrate_description_from_bullet_to_candidate_experience"
        migrate_description_from_bullet_to_candidate_experience()
        print "migration script completed successfully. Time: {}".format(time() - t)

    except Exception as e:
        print "Error: {}".format(e.message)

"""
This script will migrate all of Kaiser's existing smartlists to be owned by TalentPipelines
"""
from time import time
from candidate_service.candidate_app import app
from candidate_service.common.models.db import db
from candidate_service.common.models.user import User, Domain
from candidate_service.common.models.candidate import Candidate, CandidateExperience
from candidate_service.modules.talent_cloud_search import upload_candidate_documents


def set_experience_org_name_to_none(domain_id):
    """
    :rtype: list[int]
    """
    # Retrieve candidates from db who's organization name is set to NA
    hp_candidate_experiences = CandidateExperience.query.join(Candidate, User, Domain). \
        filter(Domain.id == domain_id).filter(CandidateExperience.organization == 'NA')

    print("total number of candidates to be processed: {}".format(hp_candidate_experiences.count()))

    for experience in hp_candidate_experiences:  # type: CandidateExperience
        # Set experience organization to None
        experience.organization = None
        db.session.commit()

    return [exp.candidate_id for exp in hp_candidate_experiences]


if __name__ == '__main__':
    start_time = time()
    try:
        # Run script only for HP (domain ID = 116)
        candidate_ids = set_experience_org_name_to_none(domain_id=116)
        upload_candidate_documents(candidate_ids)
        print("Success. Time: {}".format(time() - start_time))
    except Exception as e:
        db.session.rollback()
        print("Error: {}".format(e.message))

"""
This script will migrate all of Kaiser's existing smartlists to be owned by TalentPipelines
"""
from time import time
from candidate_service.candidate_app import app
from candidate_service.common.models.db import db
from candidate_service.common.models.user import User, Domain
from candidate_service.common.models.smartlist import Smartlist
from candidate_service.common.models.talent_pools_pipelines import TalentPipeline, TalentPool, TalentPoolCandidate
from candidate_service.common.models.candidate import Candidate
from candidate_service.modules.talent_cloud_search import upload_candidate_documents_in_domain

kaiser_domains = [90, 104]
kaiser_users = User.query.filter(User.domain_id.in_(kaiser_domains)).all()


def migrate_kaisers_smartlist():
    """
    Function will create talent pipelines from existing smart lists
    """
    for user in kaiser_users:

        smartlists = Smartlist.query.filter_by(user_id=user.id).all()
        print "***** kaiser smartlist count: {} *****".format(len(smartlists))

        for i, smartlist in enumerate(smartlists, start=1):

            smartlist_pipeline_id = smartlist.talent_pipeline_id
            smartlist_name = smartlist.name

            if not smartlist_pipeline_id:
                talent_pipeline = TalentPipeline(
                    name=smartlist_name,
                    user_id=smartlist.user_id,
                    talent_pool_id=TalentPool.query.filter_by(domain_id=user.domain_id).first().id,
                    search_params=smartlist.search_params,
                    date_needed=smartlist.added_time,
                    added_time=smartlist.added_time
                )
                db.session.add(talent_pipeline)
                print "i: {}\ttalent_pipeline_id: {}\tsmartlist_id: {}".format(i, talent_pipeline.id, smartlist.id)
                smartlist.talent_pipeline_id = talent_pipeline.id
                db.session.commit()


def set_candidate_talent_pools():
    """
    Function will link candidates to talent pools
    """
    for domain_id in kaiser_domains:

        domain_candidates = Candidate.query.join(User, Domain).filter(User.domain_id == domain_id).all()

        print "total_number_of_candidates: {}\tdomain_id: {}".format(len(domain_candidates), domain_id)

        for candidate in domain_candidates:
            candidate_id = candidate.id
            tp_candidates = TalentPoolCandidate.query.filter_by(candidate_id=candidate_id).first()
            if not tp_candidates:
                # Domain talent pool
                domain_tp = TalentPool.query.filter_by(domain_id=domain_id).first()
                db.session.add(TalentPoolCandidate(talent_pool_id=domain_tp.id, candidate_id=candidate_id))
                db.session.commit()
                print "Candidate: {} linked to TalentPool: {}".format(candidate_id, domain_tp.id)


if __name__ == '__main__':
    start = time()
    try:
        # Migrate kaiser's existing Smart List to Talent Pipelines
        print "STARTING: migrate_kaisers_smartlist"
        migrate_kaisers_smartlist()

        # Link kaiser's candidates to Talent Pools
        print "STARTING: set_candidate_talent_pools"
        set_candidate_talent_pools()

        print "Uploading candidate documents for domains 90 & 104"
        upload_candidate_documents_in_domain(kaiser_domains[0])
        upload_candidate_documents_in_domain(kaiser_domains[1])

        print "Execution completed. Total time: {}".format(time() - start)
    except Exception as e:
        db.session.rollback()
        print "ERROR: {}".format(e)

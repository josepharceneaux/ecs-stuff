"""
This script will migrate all of Kaiser's existing smartlists to be owned by TalentPipelines
"""
from time import time
from user_service.user_app import app
from user_service.common.models.db import db
from user_service.common.models.user import User
from user_service.common.models.smartlist import Smartlist
from user_service.common.models.talent_pools_pipelines import TalentPipeline, TalentPool

kaiser_domains = [90, 104]
kaiser_users = User.query.filter(User.domain_id.in_(kaiser_domains)).all()


def migrate_kaisers_smartlist():
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
                db.session.commit()

                print "i: {}\ttalent_pipeline_id: {}\tsmartlist_id: {}".format(i, talent_pipeline.id, smartlist.id)

                smartlist.talent_pipeline_id = talent_pipeline.id


if __name__ == '__main__':
    start = time()
    try:
        migrate_kaisers_smartlist()
        db.session.commit()
        print "Execution completed. Total time: {}".format(time() - start)
    except Exception as e:
        db.session.rollback()
        print "ERROR: {}".format(e)

from candidate_service.app import app, db
from flask_restful import (Api, Resource)
from candidate_service.modules.TalentCandidates import does_candidate_belong_to_user
from candidate_service.common.models.user import User

api = Api(app=app)


class CandidateResource(Resource):
    def get(self, **kwargs):
        print "kwargs = %s" % kwargs

        candidate_id = kwargs.get('id')
        # user_row = kwargs.get('user_row')

        user_row = db.session.query(User).get(1)
        print "user_row = %s" % user_row


        x = does_candidate_belong_to_user(user_row=user_row, candidate_id=candidate_id)
        print "does_candidate_belong_to_user: %s" % x
        return dict(foo=x)

api.add_resource(CandidateResource, "/v1/candidates/<id>")
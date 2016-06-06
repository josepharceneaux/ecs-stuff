# Standard library
import requests

# Flask specific
from flask_restful import Resource

# Decorators
from candidate_service.common.utils.auth_utils import require_oauth, require_all_roles

# Models
from candidate_service.common.models.candidate import CandidateStatus
from candidate_service.common.models.user import DomainRole


class CandidateStatusesResources(Resource):
    decorators = [require_oauth()]

    @require_all_roles(DomainRole.Roles.CAN_GET_CANDIDATES)
    def get(self):
        """
        Function will create candidate's status(es)
        Usage:
            >>> headers = {"Authorization": "Bearer {access_token}"}
            >>> requests.get(url="/v1/candidate_statuses", headers=headers)
            <Response [200]>
        :return:    {"statuses": [{"id": 1, "description": "New", "Notes": "newly added candidate"}, {...}]}
        """
        return {"statuses": [{
                                 "id": status.id,
                                 "description": status.description,
                                 "notes": status.notes
                             } for status in CandidateStatus.get_all()]}

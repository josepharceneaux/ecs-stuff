# Standard library
import requests

# Flask specific
from flask import request

# Graphene related
import graphene
from graph_api_service.modules.schema import CandidateType

# Models
from graph_api_service.common.models.candidate import Candidate

# Validators
from graph_api_service.common.utils.candidate_utils import get_candidate_if_validated

# Authentication & Permissions
from graph_api_service.common.utils.auth_utils import require_oauth, require_all_permissions
from graph_api_service.common.models.user import Permission

from ..dynamodb.dynamo_actions import DynamoDB


class QueryCandidate(graphene.ObjectType):
    candidate = graphene.Field(
        type=CandidateType,
        id=graphene.String()
    )

    # @require_oauth()
    # @require_all_permissions(Permission.PermissionNames.CAN_GET_CANDIDATES)
    def resolve_candidate(self, args, info):
        """
        Function will check if candidate exists or hidden using MySQL database;
        if found, it is assumed that candidate also exists in DynamoDB and will
        retrieve it therefrom

        :param args: arguments provided by the client
        """
        candidate_id = args.get('id')

        # Check if candidate exists and is not hidden
        # get_candidate_if_validated(user=request.user, candidate_id=candidate_id)

        # Retrieve candidate from DynamoDB
        return DynamoDB.get_candidate(int(candidate_id))

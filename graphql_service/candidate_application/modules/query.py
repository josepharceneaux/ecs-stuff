# Graphene related
import graphene
from graphql_service.candidate_application.modules.schema import CandidateType

from flask import request

# Authentication & Permissions
from graphql_service.common.utils.auth_utils import require_oauth

# Utilities
from graphql_service.candidate_application.dynamodb import DynamoDB

# Validations
from validators import is_candidate_validated


class CandidateQuery(graphene.ObjectType):
    candidate = graphene.Field(type=CandidateType, id=graphene.Int(required=True))

    @require_oauth()
    # @require_all_permissions(Permission.PermissionNames.CAN_GET_CANDIDATES)
    def resolve_candidate(self, args, context, info):
        """
        Function will check if candidate exists or hidden using MySQL database;
        if found, it is assumed that candidate also exists in DynamoDB and will
        retrieve it therefrom

        :param args: arguments provided by the client
        """
        candidate_id = args.get('id')

        # Return None if candidate is not found or if user is not permitted to retrieve the candidate
        if not is_candidate_validated(request.user, candidate_id):
            return None

        return DynamoDB.get_attributes(candidate_id)

# Standard library

# Flask specific

# Graphene related
import graphene

from graphql_service.candidate_application.modules.schema import CandidateType
# Models

# Validators

# Authentication & Permissions

# Utilities
from graphql_service.candidate_application.dynamodb import DynamoDB


class CandidateQuery(graphene.ObjectType):
    candidate = graphene.Field(
        type=CandidateType,
        id=graphene.Int()
    )

    # @require_oauth()
    # @require_all_permissions(Permission.PermissionNames.CAN_GET_CANDIDATES)
    def resolve_candidate(self, args, context, info):
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
        return DynamoDB.get_candidate(candidate_id)

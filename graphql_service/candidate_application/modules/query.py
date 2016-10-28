# Graphene related
import graphene
from graphql_service.candidate_application.modules.schema import CandidateType
from graphql_service.candidate_application.modules.schema_edits import EditType

# Authentication & Permissions
from graphql_service.common.models.user import User
from graphql_service.common.models.candidate_edit import CandidateEdit

# Utilities
from graphql_service.candidate_application.dynamodb import DynamoDB

# Validations
from validators import is_candidate_validated


class CandidateQuery(graphene.ObjectType):
    candidate = graphene.Field(type=CandidateType, id=graphene.Int(required=True))

    # TODO: authentication should be built using graphene mutation
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
        user = User.get(1)  # TODO: once authentication is setup, user must be retrieved via flask.request

        # Return None if candidate is not found or if user is not permitted to retrieve the candidate
        if not is_candidate_validated(user, candidate_id):
            return None

        return DynamoDB.get_candidate(candidate_id)


# TODO: use graphene-sqlalchemy library
class CandidateEditQuery(graphene.ObjectType):
    edit = graphene.Field(type=EditType, candidate_id=graphene.Int(required=True))

    def resolve_edit(self, args, context, info):
        candidate_id = args.get('candidate_id')

        user = User.get(1)  # TODO: once authentication is setup, user must be retrieved via flask.request

        # Return None if candidate is not found or if user is not permitted to retrieve the candidate
        if not is_candidate_validated(user, candidate_id):
            return None

        return CandidateEdit.get_query(id=candidate_id, context=context, info=info)

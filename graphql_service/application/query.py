import graphene
from graphql_service.candidate_application.modules.query import CandidateQuery, CandidateEditQuery
from graphql_service.user_application.query import UserQuery

# Inline Function for nested functions
query_field = lambda x: graphene.Field(type=x, resolver=lambda *args: x())


class Query(graphene.ObjectType):
    node = graphene.relay.Node.Field()
    candidate_query = query_field(CandidateQuery)
    candidate_edit_query = query_field(CandidateEditQuery)
    user_query = query_field(UserQuery)


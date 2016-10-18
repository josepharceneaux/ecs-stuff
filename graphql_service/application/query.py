import graphene
from graphql_service.candidate_application.modules.query import CandidateQuery
from graphql_service.user_application.query import UserQuery

# Inline Function for nested functions
query_field = lambda x: graphene.Field(type=x, resolver=lambda *args: x())


class Query(graphene.ObjectType):
    node = graphene.relay.Node.Field()
    candidate_query = query_field(CandidateQuery)
    user_query = query_field(UserQuery)


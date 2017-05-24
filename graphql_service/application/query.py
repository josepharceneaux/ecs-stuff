"""
Here we have base Query class
"""
# Third Party
import graphene

# Application Specific
from graphql_service.candidate_application.modules.query import CandidateQuery

# Inline Function for nested functions
query_field = lambda x: graphene.Field(type=x, resolver=lambda *args: x())


class Query(graphene.ObjectType):
    node = graphene.relay.Node.Field()
    candidate_query = query_field(CandidateQuery)

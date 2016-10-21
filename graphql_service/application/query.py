"""
Here we have base Query class
"""

# Third Party
import graphene

# Application Specific
from graphql_service.user_application.query import UserQuery
from graphql_service.candidate_application.modules.query import CandidateQuery
from graphql_service.email_campaign_application.query import EmailCampaignQuery


# Inline Function for nested functions
query_field = lambda x: graphene.Field(type=x, resolver=lambda *args: x())


class Query(graphene.ObjectType):
    node = graphene.relay.Node.Field()
    candidate_query = query_field(CandidateQuery)
    user_query = query_field(UserQuery)
    email_campaign_query = query_field(EmailCampaignQuery)

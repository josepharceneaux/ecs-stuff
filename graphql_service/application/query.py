"""
Here we have base Query class
"""
# Third Party
import graphene

# Application Specific
from graphql_service.user_application.query import UserQuery
from graphql_service.email_campaign_application.query import EmailCampaignQuery
from graphql_service.candidate_application.modules.query import (CandidateQuery, CandidateEditQuery)


# Inline Function for nested functions
query_field = lambda x: graphene.Field(type=x, resolver=lambda *args: x())


class Query(graphene.ObjectType):
    node = graphene.relay.Node.Field()
    candidate_query = query_field(CandidateQuery)
    candidate_edit_query = query_field(CandidateEditQuery)
    user_query = query_field(UserQuery)
    email_campaign_query = query_field(EmailCampaignQuery)

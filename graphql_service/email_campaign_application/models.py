"""
Here we have Types defined for models of email-campaign=service
"""
# Third Party
import graphene
from graphene_sqlalchemy import SQLAlchemyObjectType

# Application Specific
from graphql_service.common.models.email_campaign import (EmailCampaign, EmailCampaignBlast)


class SortBy(graphene.Enum):
    name = 'name'
    added_datetime = 'added_datetime'


class SortTypes(graphene.Enum):
    ASC = 'ASC'
    DESC = 'DESC'


class EmailCampaignType(SQLAlchemyObjectType):

    class Meta:
        model = EmailCampaign


class EmailCampaignBlastsType(SQLAlchemyObjectType):

    class Meta:
        model = EmailCampaignBlast

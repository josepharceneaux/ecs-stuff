"""
Here we have Types defined for models of email-campaign-service
"""

__author__ = 'basit'

# Third Party
import graphene
from graphene import relay
from graphene_sqlalchemy import SQLAlchemyObjectType

# Application Specific
from ..models.email_campaign import (EmailCampaign, EmailCampaignBlast, EmailCampaignSend)


class SortBy(graphene.Enum):
    name = 'name'
    added_datetime = 'added_datetime'


class SortTypes(graphene.Enum):
    ASC = 'ASC'
    DESC = 'DESC'


class EmailCampaignType(SQLAlchemyObjectType):

    class Meta:
        model = EmailCampaign
        interfaces = (relay.Node,)


class EmailCampaignBlastType(SQLAlchemyObjectType):

    class Meta:
        model = EmailCampaignBlast
        interfaces = (relay.Node,)


class EmailCampaignSendType(SQLAlchemyObjectType):

    class Meta:
        model = EmailCampaignSend
        interfaces = (relay.Node,)

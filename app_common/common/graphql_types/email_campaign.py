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
    """
    Allowed values by which email-campaigns can be sorted.
    Default is set to `added_datetime`.
    """
    name = 'name'
    added_datetime = 'added_datetime'


class SortTypes(graphene.Enum):
    """
    Allowed values by which email-campaigns can be sorted in ascending or descending order.
    Default is set to `DESC`.
    """
    ASC = 'ASC'
    DESC = 'DESC'


class EmailCampaignType(SQLAlchemyObjectType):
    """
    SQLAlchemyObjectType for EmailCampaign model.
    """

    class Meta:
        model = EmailCampaign
        interfaces = (relay.Node,)


class EmailCampaignBlastType(SQLAlchemyObjectType):
    """
    SQLAlchemyObjectType for EmailCampaignBlast model.
    """

    class Meta:
        model = EmailCampaignBlast
        interfaces = (relay.Node,)


class EmailCampaignSendType(SQLAlchemyObjectType):
    """
    SQLAlchemyObjectType for EmailCampaignSend model.
    """

    class Meta:
        model = EmailCampaignSend
        interfaces = (relay.Node,)

"""
Here we have Query class for email-campaign-service
"""

# Third Party
import graphene
from graphene_sqlalchemy import SQLAlchemyConnectionField

# Common Utils
from email_campaign_service.common.utils.auth_utils import require_oauth
from email_campaign_service.common.models.email_campaign import EmailCampaign
from email_campaign_service.common.campaign_services.campaign_base import CampaignBase
from email_campaign_service.common.campaign_services.campaign_utils import CampaignUtils
from email_campaign_service.common.graphql_types.email_campaign import (EmailCampaignType, SortBy, SortTypes,
                                                                        EmailCampaignBlastsType)

# Application Specific
from graphql_service.common.error_handling import (NotFoundError, ForbiddenError)
# from graphql_service.common.utils.api_utils import (get_paginated_list, DEFAULT_PAGE, DEFAULT_PAGE_SIZE)


class EmailCampaignQuery(graphene.ObjectType):
    campaigns = SQLAlchemyConnectionField(EmailCampaignType,
                                          sort_type=SortTypes(), search=graphene.String(),
                                          sort_by=SortBy(), is_hidden=graphene.Int())
    # email_campaigns = graphene.List(EmailCampaignType, page=graphene.Int(), per_page=graphene.Int(),
    #                                 sort_type=SortTypes(), search=graphene.String(),
    #                                 sort_by=SortBy(), is_hidden=graphene.Int())
    campaign = graphene.Field(type=EmailCampaignType, id=graphene.Int())
    blasts = SQLAlchemyConnectionField(EmailCampaignBlastsType, campaign_id=graphene.Int())
    blast = graphene.Field(type=EmailCampaignBlastsType, campaign_id=graphene.Int(), id=graphene.Int())

    @require_oauth()
    def resolve_campaigns(self, args, request, info):
        # page = args.get('page', DEFAULT_PAGE)
        # per_page = args.get('per_page', DEFAULT_PAGE_SIZE)
        sort_type = args.get('sort_type', 'DESC')
        search_keyword = args.get('search', '')
        sort_by = args.get('sort_by', 'added_datetime')
        is_hidden = args.get('is_hidden', 0)
        # Get all email campaigns from logged in user's domain
        query = EmailCampaign.get_by_domain_id_and_filter_by_name(request.user.domain_id,
                                                                  search_keyword, sort_by,
                                                                  sort_type, int(is_hidden))
        return query

    @require_oauth()
    def resolve_campaign(self, args, request, info):
        email_campaign_id = args.get('id')
        email_campaign = EmailCampaignType.get_node(id=email_campaign_id, context=request, info=info)
        # email_campaign = EmailCampaign.get_by_id(email_campaign_id)
        if not email_campaign:
            raise NotFoundError("Email campaign with id: %s does not exist" % email_campaign_id)
        if not email_campaign.user.domain_id == request.user.domain_id:
            raise ForbiddenError("Email campaign doesn't belongs to user's domain")
        return email_campaign

    @require_oauth()
    def resolve_blasts(self, args, request, info):
        # page = args.get('page', DEFAULT_PAGE)
        # per_page = args.get('per_page', DEFAULT_PAGE_SIZE)
        email_campaign_id = args.get('campaign_id')
        # Get campaign object
        campaign = CampaignBase.get_campaign_if_domain_is_valid(email_campaign_id, request.user, CampaignUtils.EMAIL)
        return campaign.blasts

    @require_oauth()
    def resolve_blast(self, args, request, info):
        blast_id = args.get('id')
        email_campaign_id = args.get('campaign_id')
        blast_obj = CampaignBase.get_valid_blast_obj(email_campaign_id, blast_id, request.user, CampaignUtils.EMAIL)
        return blast_obj

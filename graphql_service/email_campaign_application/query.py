"""
Here we have Query class for email-campaign-service
"""

# Third Party
import graphene

# Application Specific
from graphql_service.common.models.email_campaign import EmailCampaign
from graphql_service.common.error_handling import (NotFoundError, ForbiddenError)
from graphql_service.email_campaign_application.models import (EmailCampaignType, SortBy, SortTypes)
from graphql_service.common.utils.api_utils import (get_paginated_list, DEFAULT_PAGE, DEFAULT_PAGE_SIZE)


class EmailCampaignQuery(graphene.ObjectType):
    email_campaigns = graphene.List(EmailCampaignType, page=graphene.Int(), per_page=graphene.Int(),
                                    sort_type=SortTypes(), search=graphene.String(),
                                    sort_by=SortBy(), is_hidden=graphene.Int())
    email_campaign = graphene.Field(type=EmailCampaignType, id=graphene.Int())

    def resolve_email_campaigns(self, args, request, info):
        page = args.get('page', DEFAULT_PAGE)
        per_page = args.get('per_page', DEFAULT_PAGE_SIZE)
        sort_type = args.get('sort_type', 'DESC')
        search_keyword = args.get('search', '')
        sort_by = args.get('sort_by', 'added_datetime')
        is_hidden = args.get('is_hidden', 0)

        # Get all email campaigns from logged in user's domain
        query = EmailCampaign.get_by_domain_id_and_filter_by_name(request.user.domain_id,
                                                                  search_keyword, sort_by,
                                                                  sort_type, int(is_hidden))
        return get_paginated_list(query, page, per_page).items

    def resolve_email_campaign(self, args, request, info):
        email_campaign_id = args.get('id')
        email_campaign = EmailCampaign.get_by_id(email_campaign_id)
        if not email_campaign:
            raise NotFoundError("Email campaign with id: %s does not exist" % email_campaign_id)
        if not email_campaign.user.domain_id == request.user.domain_id:
            raise ForbiddenError("Email campaign doesn't belongs to user's domain")
        return email_campaign

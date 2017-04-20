# 3rd party imports
from flask import Blueprint
from flask import request
from flask_restful import Resource
# Common imports
from user_service.common.models.misc import CustomField
from user_service.common.routes import UserServiceApi
from user_service.common.talent_api import TalentApi
from user_service.common.utils.api_utils import ApiResponse
from user_service.common.utils.auth_utils import require_oauth, require_all_permissions, Permission


class SearchDomainCustomFieldResource(Resource):
    decorators = [require_oauth()]

    @require_all_permissions(Permission.PermissionNames.CAN_GET_DOMAIN_CUSTOM_FIELDS)
    def get(self):
        """
        Search custom fields based on given filter criteria
        """
        # Authenticated user
        authed_user = request.user
        search_query = request.args.get('query', '')
        sort_type = request.args.get('sort_type', 'DESC')
        sort_by = request.args.get('sort_by', 'added_time')
        cf_type = request.args.get('type', 'all')

        query_object = CustomField.get_by_domain_id_and_filter_by_name_and_type(authed_user.domain.id, search_query,
                                                                                sort_by, sort_type, cf_type)
        items = [field.to_json() for field in query_object]
        response = {'custom_fields': items}
        return ApiResponse(response)

cf_search_blueprint = Blueprint('domain_cf_search_api', __name__)
api = TalentApi(cf_search_blueprint)
api.add_resource(SearchDomainCustomFieldResource, UserServiceApi.DOMAIN_CUSTOM_FIELD_SEARCH)

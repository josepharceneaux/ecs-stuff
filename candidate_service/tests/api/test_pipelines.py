# # Candidate Service app instance
# from candidate_service.candidate_app import app
#
# # Conftest
# from candidate_service.common.tests.conftest import *
#
# # Custom Errors
# from candidate_service.custom_error_codes import CandidateCustomErrors as custom_errors
#
# # Helper functions
# from helpers import AddUserRoles
# from candidate_service.common.routes import CandidateApiUrl
# from candidate_service.common.utils.test_utils import send_request, response_info
#
# from candidate_service.common.utils.handy_functions import add_role_to_test_user
# from candidate_service.common.models.user import DomainRole
#
#
# class TestGetCandidatePipelines(object):
#     OK = 200
#     URL = CandidateApiUrl.PIPELINES
#     CANDIDATE_URL = CandidateApiUrl.CANDIDATES
#
#     def test_get_pipelines(self, access_token_first, user_first, candidate_first):
#         """
#         Test: Retrieve candidate's pipelines in order of creation, most recent first
#         """
#         # Add user roles
#         AddUserRoles.all_roles(user_first)
#         add_role_to_test_user(user_first, [DomainRole.Roles.CAN_GET_TALENT_PIPELINES])
#
#         # Create candidate  TODO
#         # create_resp = send_request('post', )
#
#         get_resp = send_request('get', CandidateApiUrl.PIPELINES % candidate_first.id, access_token_first)
#         print response_info(get_resp)

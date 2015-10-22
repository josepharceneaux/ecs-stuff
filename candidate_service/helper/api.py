from candidate_service.app import logger
import json


# def parse_request_body():
#     """
#     :rtype: dict[str, T]
#     """
#     request_body = ''
#     try:
#         request_body = request.body.read()
#         logger.info('api/%s/%s: Received request body: %s',
#                     request.function, request.env.request_method, request_body)
#         body_dict = json.loads(request_body)
#     except Exception:
#         logger.exception('api/%s/%s: Received request body: %s',
#                          request.function, request.env.request_method, request_body)
#         response.status = 400
#         return CustomErrorResponse.make_response_with_text(CustomErrorResponse.MUST_BE_JSON_DICT,
#                                                            "Unable to parse request body as JSON")
#
#     # Request body must be a JSON dict
#     if not isinstance(body_dict, dict):
#         response.status = 400
#         return CustomErrorResponse.MUST_BE_JSON_DICT
#
#     # Request body cannot be empty
#     if not any(body_dict):
#         response.status = 400
#         return CustomErrorResponse.make_response_with_text(CustomErrorResponse.MISSING_INPUT, "Request body cannot be empty")
#
#     return body_dict


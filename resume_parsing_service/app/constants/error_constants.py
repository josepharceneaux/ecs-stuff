"""Resume parsing specific error codes and messages."""


# Multi Purpose Messages
GENERIC_ERROR_MSG = 'There seems to have been an error in parsing your file, please try again. If it continues to happen please contact customer support.'
FILE_TYPE_MSG = 'It looks like you have uploaded an invalid file. Please check to make sure your file type is correct and re-upload.'
GT_ISSUE_MSG = 'There seems to have been an error on our side, please try again. If it continues to happen please contact customer support.'


# Invalid inputs
INVALID_HEADERS = {
    'code': 3000,
    'message': GT_ISSUE_MSG
}

INVALID_FILE_TYPE = {
    'code': 3001,
    'message': FILE_TYPE_MSG
}

JSON_SCHEMA_ERROR = {
    'code': 3002, # unused currently. Would require updates to get_json_data_if_validated
    'message': GT_ISSUE_MSG
}

INVALID_ARGS = {
    'code': 3003,
    'message': GT_ISSUE_MSG
}

INVALID_ARGS_MOBILE = {
    'code': 3004,
    'message': GENERIC_ERROR_MSG
}

NO_TP_ARG = {
    'code': 3005,
    'message': 'Please contact customer support.'
}

NO_TEXT_EXTRACTED = {
    'code': 3006,
    'message': FILE_TYPE_MSG
}

ERROR_DECODING_TEXT = {
    'code': 3007,
    'message': GENERIC_ERROR_MSG
}

ERROR_ENCODING_TEXT = {
    'code': 3008,
    'message': GENERIC_ERROR_MSG
}

ENCRYPTED_PDF = {
    'code': 3009,
    'message': 'The PDF appears to be encrypted and could not be read. Please try using an un-encrypted PDF.'
}


# Issues with third party tools.
GOOGLE_OCR_UNAVAILABLE = {
    'code': 3100,
    'message': GENERIC_ERROR_MSG
}

GOOGLE_OCR_ERROR = {
    'code': 3101,
    'message': GENERIC_ERROR_MSG
}

ABBYY_UNABLE_TO_QUEUE = {
    'code': 3102,
    'message': GENERIC_ERROR_MSG
}

ABBYY_CREDITS = {
    'code': 3103,
    'message': GENERIC_ERROR_MSG
}

ABBYY_MAX_ATTEMPTS = {
    'code': 3104,
    'message': GENERIC_ERROR_MSG
}

ABBYY_UNAVAILABLE = {
    'code': 3105,
    'message': GENERIC_ERROR_MSG
}

BG_UNAVAILABLE = {
    'code': 3106,
    'message': GENERIC_ERROR_MSG
}

BG_NO_PARSED_TEXT = {
    'code': 3107,
    'message': FILE_TYPE_MSG
}


# Issues with internal services
CANDIDATE_POST_CONNECTION = {
    'code': 3200,
    'message': 'An error has occurred in creating the candidate you requested. Please try again.'
}

CANDIDATE_POST_ERROR = {
    'code': 3201,
    'message': 'An error has occurred in creating the candidate you requested. Please try again.'
}

CANDIDATE_PATCH_CONNECTION = {
    'code': 3202,
    'message': 'An error has occurred in updating the candidate you requested. Please try again.'
}

CANDIDATE_PATCH_GENERIC = {
    'code': 3203,
    'message': 'An error has occurred in updating the candidate you requested. Please try again.'
}

CANDIDATE_GET = {
    'code': 3204,
    'message': 'An error has occurred in retreiving the candidate you created. Please try again.'
}

RESUME_UNCAUGHT_EXCEPTION = {
    'code': 3205,
    'message': GT_ISSUE_MSG
}

TALENT_POOLS_GET = {
    'code': 3206,
    'message': GENERIC_ERROR_MSG
}

TALENT_POOLS_ERROR = {
    'code': 3207,
    'message': GENERIC_ERROR_MSG
}

CANDIDATE_5XX = {
    'code': 3208,
    'message': GT_ISSUE_MSG
}
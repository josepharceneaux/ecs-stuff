"""
Author: Hafiz Muhammad Basit, QC-Technologies, <basit.gettalent@gmail.com>

This file contains custom error codes  for campaign services like Email campaign-service

    Range: 1401 -- 1499

"""
# Email campaign custom errors, range 1401-1450

# Campaigns 1401 - 1430

# General messages 1401-1405
EMAIL_CAMPAIGN_FORBIDDEN = ("Email campaign doesn't belongs to user's domain", 1401)
EMAIL_CAMPAIGN_NOT_FOUND = ("Email campaign not found", 1402)
ERROR_SENDING_EMAIL = ("Error occurred while sending email to given address(es)", 1403)

# Input Validations 1406 - 1420
INVALID_VALUE_OF_PAGINATION_PARAM = ("Invalid value for pagination param", 1406)
INVALID_VALUE_OF_QUERY_PARAM = ("Invalid value of query param", 1407)
INVALID_REQUEST_BODY = ("Received invalid request body", 1408)
NOT_NON_ZERO_NUMBER = ("Expecting positive int|long value for {}", 1409)
MISSING_FIELD = ("{} field is required", 1410)
INVALID_INPUT = ("Got invalid value for {}", 1411)
INVALID_DATETIME_VALUE = ("Expecting datetime value to be in future", 1412)
INVALID_DATETIME_FORMAT = ("Expecting ISO8601_FORMAT of datetime", 1413)
SMARTLIST_FORBIDDEN = ("Smartlist doesn't belongs to user's domain", 1414)
SMARTLIST_NOT_FOUND = ("Smartlist not found", 1415)
NO_SMARTLIST_ASSOCIATED_WITH_CAMPAIGN = ("No smartlist is associated with the campaign", 1416)
NO_VALID_CANDIDATE_FOUND = ("No candidate with email(s) found for smartlist(s) associated with the campaign", 1417)

# Blasts 1421-1430
EMAIL_CAMPAIGN_BLAST_FORBIDDEN = ("Requested blast doesn't belongs to user's domain", 1421)
EMAIL_CAMPAIGN_BLAST_NOT_FOUND = ("Requested blast not found", 1422)

# Sends 1431-1440
EMAIL_CAMPAIGN_SEND_FORBIDDEN = ("Requested blast doesn't belongs to user's domain", 1431)
EMAIL_CAMPAIGN_SEND_NOT_FOUND = ("Requested blast not found", 1432)

# Clients 1441-1450
EMAIL_CLIENT_FORBIDDEN = ("Email client does not belong to user`s domain", 1441)
EMAIL_CLIENT_NOT_FOUND = ("Email client not found", 1442)

# Email templates custom errors, range 1451-1470
TEMPLATES_FEATURE_NOT_ALLOWED = ("You are not allowed to view this feature", 1451)
DUPLICATE_TEMPLATE_FOLDER_NAME = ("Template folder with given name already exists", 1452)
TEMPLATE_FOLDER_FORBIDDEN = ("Requested template folder is not owned by user's domain", 1453)
TEMPLATE_FOLDER_NOT_FOUND = ("Requested template folder not found", 1454)
DUPLICATE_TEMPLATE_NAME = ("Email template with given name already exists", 1455)
EMAIL_TEMPLATE_FORBIDDEN = ("Requested email template is not owned by user's domain", 1456)
EMAIL_TEMPLATE_NOT_FOUND = ("Requested email template not found", 1457)

# Base campaign custom errors, range 1471-1480
BASE_CAMPAIGN_ORPHANED = ("Requested Base campaign is orphaned", 1471)

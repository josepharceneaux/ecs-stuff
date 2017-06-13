"""
Author: Hafiz Muhammad Basit, QC-Technologies, <basit.gettalent@gmail.com>

This file contains custom error codes  for campaign services like Email campaign-service

    Range: 1401 -- 1499

"""
# Email campaign custom errors, range 1401-1450

# Campaigns 1401-1430
EMAIL_CAMPAIGN_FORBIDDEN = ("Email campaign doesn't belongs to user's domain", 1401)
EMAIL_CAMPAIGN_NOT_FOUND = ("Email campaign not found", 1402)

# Input Validations
INVALID_VALUE_OF_PAGINATION_PARAM = ("Invalid value for pagination param", 1403)
INVALID_VALUE_OF_QUERY_PARAM = ("Invalid value of query param", 1404)
INVALID_REQUEST_BODY = ("Received invalid request body", 1405)
NOT_NON_ZERO_NUMBER = ("Expecting positive int|long value for {}", 1406)
MISSING_FIELD = ("{} field is required", 1407)
INVALID_INPUT = ("Got invalid value for {}", 1408)
INVALID_DATETIME_VALUE = ("Expecting datetime value to be in future", 1409)
INVALID_DATETIME_FORMAT = ("Expecting ISO8601_FORMAT of datetime", 1410)
SMARTLIST_FORBIDDEN = ("Smartlist doesn't belongs to user's domain", 1411)
SMARTLIST_NOT_FOUND = ("Smartlist not found", 1412)

# Blasts 1421-1430
EMAIL_CAMPAIGN_BLAST_FORBIDDEN = ("Requested blast doesn't belongs to user's domain", 1421)
EMAIL_CAMPAIGN_BLAST_NOT_FOUND = ("Requested blast not found", 1422)

# Sends 1431-1440
EMAIL_CAMPAIGN_SEND_FORBIDDEN = ("Requested blast doesn't belongs to user's domain", 1431)
EMAIL_CAMPAIGN_SEND_NOT_FOUND = ("Requested blast not found", 1432)

# Clients 1441-1450
EMAIL_CLIENT_FORBIDDEN = ("Email client not found", 1441)
EMAIL_CLIENT_NOT_FOUND = ("Email client not found", 1442)

# Email templates custom errors, range 1451-1470
TEMPLATES_FEATURE_NOT_ALLOWED = ("You are not allowed to view this feature", 1451)
DUPLICATE_TEMPLATE_FOLDER_NAME = ("Template folder with given name already exists", 1452)
TEMPLATE_FOLDER_FORBIDDEN = ("Requested template folder is not owned by user's domain", 1453)
TEMPLATE_FOLDER_NOT_FOUND = ("Requested template folder not found", 1454)

# Base campaign custom errors, range 1471-1480
BASE_CAMPAIGN_ORPHANED = ("Requested Base campaign is orphaned", 1471)

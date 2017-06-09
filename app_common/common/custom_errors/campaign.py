"""
Author: Hafiz Muhammad Basit, QC-Technologies, <basit.gettalent@gmail.com>

This file contains custom error codes  for campaign services like Email campaign-service

    Range: 1401 -- 1499

"""

# Email campaign custom errors, range 1401-1450
EMAIL_CAMPAIGN_FORBIDDEN = ("Email campaign doesn't belongs to user's domain", 1401)
EMAIL_CAMPAIGN_NOT_FOUND = ("Email campaign not found", 1402)
EMAIL_CAMPAIGN_BLAST_FORBIDDEN = ("Requested blast doesn't belongs to user's domain", 1403)
EMAIL_CAMPAIGN_BLAST_NOT_FOUND = ("Requested blast not found", 1404)
EMAIL_CAMPAIGN_SEND_FORBIDDEN = ("Requested blast doesn't belongs to user's domain", 1405)
EMAIL_CAMPAIGN_SEND_NOT_FOUND = ("Requested blast not found", 1406)
EMAIL_CLIENT_FORBIDDEN = ("Email client not found", 1407)
EMAIL_CLIENT_NOT_FOUND = ("Email client not found", 1408)

# Input Validations
NOT_POSITIVE_NUMBER = ("Expecting positive int|long", 1403)
MISSING_FIELD = ("{} field is required", 1401)
NOT_NUMBER = ("Campaign {} can not be a number", 1403)
INVALID_DATETIME_VALUE = ("Expecting datetime value to be in future", 1404)
NON_EXISTING_ENTITY = ("Resource {} not found in database", 1405)
INVALID_INPUT = ("Got invalid value for {}", 1406)

# Email templates custom errors, range 1451-1470
TEMPLATES_FEATURE_NOT_ALLOWED = ("You are not allowed to view this feature", 1451)
DUPLICATE_TEMPLATE_FOLDER_NAME = ("Template folder with given name already exists", 1452)
TEMPLATE_FOLDER_FORBIDDEN = ("Requested template folder is not owned by user's domain", 1453)
TEMPLATE_FOLDER_NOT_FOUND = ("Requested template folder not found", 1454)

# Base campaign custom errors, range 1471-1480
BASE_CAMPAIGN_ORPHANED = ("Requested Base campaign is orphaned", 1471)

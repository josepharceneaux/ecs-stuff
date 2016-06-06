"""
This is the base set of lambda handlers. The end result feature set should be to have 4 endpoints.
These endpoints will be the combonations of consuming:
    1) FilePicker Keys -or- binaries
    2) Creating a candidate or simply parsing a resume

Each handler will pull code from the resume parser library/modules and act accordingly.
"""
__author__ = 'erik@gettalent.com'

import boto3

BUCKET = 'some bucket'

def s3_parsing(event, context):
    """
    MVP checklist:
        Get s3 key
        Get object
        Send to BG
        parse response
    """
    boto_client = boto3.client('s3')
    s3_key = event['s3_key']

    resume_file = boto_client.get_object(Bucket=BUCKET, Key=s3_key)
    pass


# def s3_creation(event, context):
#     pass
#
#
# def file_parsing(event, context):
#     pass
#
#
# def file_creation(event, context):
#     pass
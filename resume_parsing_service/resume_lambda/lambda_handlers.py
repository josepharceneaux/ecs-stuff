"""
This is the base set of lambda handlers. The end result feature set should be to have 4 endpoints.
These endpoints will be the combonations of consuming:
    1) FilePicker Keys -or- binaries
    2) Creating a candidate or simply parsing a resume

Each handler will pull code from the resume parser library/modules and act accordingly.
"""
__author__ = 'erik@gettalent.com'

from boto_utils import get_s3_obj
from burning_glass_utils import fetch_optic_response
from optic_parsing_utils import parse_optic_xml
import base64
import time

def s3_parsing(event, context):
    """
    MVP checklist:
        Get s3 key DONE
        Get object DONE
        Send to BG DONE
        parse response
    """
    start = time.time()
    s3_key = event['s3_key']
    resume_file = get_s3_obj(s3_key)
    print 'Obtained resume file in {}s'.format(time.time() - start)

    doc_content = resume_file['Body'].read()
    encoded_doc = base64.b64encode(doc_content)
    print 'File encoded in {}s'.format(time.time() - start)

    bg_response = fetch_optic_response(encoded_doc)
    print 'BG response retrieved in {}s'.format(time.time() - start)

    candidate = parse_optic_xml(bg_response)
    print 'Candidate parsed in {}s'.format(time.time() - start)
    return candidate


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
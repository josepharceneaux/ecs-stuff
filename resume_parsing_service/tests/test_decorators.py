from cStringIO import StringIO

from boto3 import client
import pytest

from resume_parsing_service.app import app
from resume_parsing_service.app.views.decorators import upload_failed_IO
from resume_parsing_service.common.error_handling import InternalServerError
from resume_parsing_service.common.utils.talent_s3 import boto3_get_file


def test_catch_all_decorator():
    """
    This test case tries to emulate an uncaught exception in resumes parsing service and tests that
    the file is uploaded to the proper s3 bucket and key path.
    """
    FAIL_KEY = 'potato'
    FAIL_KEYPATH = 'FailedResumes/' + FAIL_KEY
    FAIL_CONTENTS = 'all your base are belong to us'
    FAIL_FILE = StringIO(FAIL_CONTENTS)
    FAIL_BUCKET = app.config['S3_BUCKET_NAME']
    s3_client = client('s3')

    with app.app_context():
        with pytest.raises(InternalServerError): #  This is the error expected from upload_failed_IO
            @upload_failed_IO
            def this_should_fail(empty, key_string):
                1 / 0 #  The uncaught exception...

            this_should_fail(FAIL_FILE, FAIL_KEY)
            FAIL_FILE.close()

        #  assert the item can be retrieved from s3
        fail_obj = boto3_get_file(FAIL_BUCKET, FAIL_KEYPATH)
        assert fail_obj.read() == FAIL_CONTENTS
        #  delete from s3 to ensure next run is not a false positive.
        s3_client.delete_object(Bucket=FAIL_BUCKET, Key=FAIL_KEYPATH)

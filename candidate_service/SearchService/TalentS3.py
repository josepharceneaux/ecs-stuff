# -*- coding: utf-8 -*-

import boto
import boto.exception
from boto.s3.bucket import Bucket
from boto.s3.key import Key
from boto.s3.connection import OrdinaryCallingFormat, S3Connection
import TalentPropertyManager

AWS_ACCESS_KEY_ID = 'AKIAI3422SZ6SL46EYBQ'
AWS_SECRET_ACCESS_KEY = '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'


def get_s3_bucket_and_conn():
    """

    :rtype: (Bucket, S3Connection)
    """
    c = get_s3_conn()
    bucket_name = current.TCS_BUCKET_NAME
    b = c.get_bucket(bucket_name, validate=False)
    return b, c


def get_s3_filepicker_bucket_and_conn():
    """

    :rtype: (Bucket, S3Connection)
    """
    c = get_s3_conn('us-west-1')  # gettalent-filepicker bucket is used in all environments (dev/qa/prod), so must specify region
    bucket_name = current.FILEPICKER_BUCKET_NAME
    b = c.get_bucket(bucket_name, validate=False)
    return b, c


def download_file(bucket, key_name):
    """

    :type bucket: Bucket
    :type key_name: str
    :rtype: StringIO.StringIO
    """

    key_obj = bucket.get_key(key_name=key_name)
    """
    :type: boto.s3.key.Key | None
    """
    if not key_obj:
        raise Exception("No S3 key found in bucket %s, key_name=%s", bucket, key_name)
    from StringIO import StringIO

    return StringIO(key_obj.get_contents_as_string())


def get_s3_conn(region=None):
    """

    :rtype: None | S3Connection
    """
    aws_access_key_id = current.AWS_ACCESS_KEY_ID
    aws_secret_access_key = current.AWS_SECRET_ACCESS_KEY
    region = region or TalentPropertyManager.get_s3_region()

    connection = boto.s3.connect_to_region(region,
                                           aws_access_key_id=aws_access_key_id,
                                           aws_secret_access_key=aws_secret_access_key,
                                           calling_format=OrdinaryCallingFormat())

    return connection


def get_s3_url(folder_path, name):
    """

    :rtype: str
    """
    import os

    b, c = get_s3_bucket_and_conn()
    # Query-string authentication
    bucket_name = current.TCS_BUCKET_NAME
    return c.generate_url(
        expires_in=3600 * 24 * 365,  # expires in 1 year, lol
        method='GET',
        bucket=bucket_name,
        key="%s/%s" % (folder_path, os.path.basename(name)),
        query_auth=True
    )


def is_file_existing(folder_path, name):
    import os

    b, c = get_s3_bucket_and_conn()
    k = Key(b)
    k.key = '%s/%s' % (folder_path, os.path.basename(name))
    return k.exists()


def upload_to_s3(file_content, folder_path, name, public=False):
    """
    Uploads given file object to S3.

    :param file_content: Content of file to upload
    :type file_content: str

    :param folder_path: The folder path (not bucket)
    :type folder_path: str

    :param name: Name of S3 key, after folder_path
    :type name: str

    :param public: Set whether it's public-read
    :type public: boolean

    :return: URL used to upload to S3
    :rtype: (str, Key)
    """
    import os
    current.logger.info("upload_to_s3: Uploading %s/%s of length=%s to S3", folder_path, name, len(file_content))

    name = str(name)  # in case filename is number (like candidate id)

    b, c = get_s3_bucket_and_conn()

    k = Key(b)
    key_name = '%s/%s' % (folder_path, os.path.basename(name))
    k.key = key_name
    policy = 'public-read' if public else None
    k.set_contents_from_string(file_content, policy=policy)

    # Set Content-Type headers
    if name.endswith('pdf'):
        k.set_metadata('Content-Type', 'application/pdf')  # default is application/octet-stream, but doesn't work on Chrome with PDFs
    elif name.endswith('doc'):
        k.set_metadata('Content-Type', 'application/msword')
    elif name.endswith('csv'):
        k.set_metadata('Content-Type', 'text/csv')

    # Query-string authentication
    bucket_name = current.TCS_BUCKET_NAME
    url = c.generate_url(
        expires_in=3600 * 24 * 365,  # expires in 1 year, lol
        method='GET',
        bucket=bucket_name,
        key=k.key,
        query_auth=True
    )

    return url, k


def upload_to_filepicker_s3(file_content, file_name):
    current.logger.info("upload_to_filepicker_s3: Uploading %s of length=%s to S3", file_name, len(file_content))
    b, c = get_s3_filepicker_bucket_and_conn()
    k = Key(b)
    k.key = file_name
    k.set_contents_from_string(file_content)
    import mimetypes
    mimetypes.init()
    k.set_metadata('Content-Type', mimetypes.guess_type(file_name[0]))
    return k

# Filename includes extension. Returns False if no key.
def delete_from_s3(filename, folder_path, prefix=False):
    import os

    filename = str(filename)  # in case filename is number (like candidate id)

    b, c = get_s3_bucket_and_conn()

    key_name = '%s/%s' % (folder_path, os.path.basename(filename))
    if prefix:
        for k in b.list(prefix=key_name):
            b.delete_key(k)
    else:
        k = b.get_key(key_name)
        if k:
            b.delete_key(k)


def create_bucket():
    """

    :rtype: Bucket
    """
    connection = get_s3_conn()
    name = TalentPropertyManager.get_s3_bucket_name()
    region = TalentPropertyManager.get_s3_region()
    # Only create if doesn't exist
    bucket = connection.lookup(name)
    if not bucket:
        try:
            print "Bucket doesn't exists, Trying to create a bucket with name: %s in region: %s" % (name, region)
            bucket = connection.create_bucket(bucket_name=name, location=region)
        except boto.exception.S3CreateError as s3_create_error:
            # If the error says that the bucket is already owned by you, ignore
            error_body = s3_create_error.body
            import xml.etree.ElementTree

            error_body_xml = xml.etree.ElementTree.fromstring(error_body)
            print "Error occurred while creating bucket: %s" % error_body_xml.find('Message').text
            if error_body_xml.find('Code').text != 'BucketAlreadyOwnedByYou':
                current.logger.exception("Could not create bucket with name %s in region: %s" % (name, region))
    return bucket

import boto3


BUCKET = 'tcs-local-erik'
boto_client = boto3.client('s3')


def get_s3_obj(key):
    return boto_client.get_object(Bucket=BUCKET, Key=key)

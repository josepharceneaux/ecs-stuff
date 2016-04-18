"""Python logic for dealing with sent emails stored in s3."""
import urllib
import boto3
import email

RESUMES_BUCKET = 'resume-emails'

s3_client = boto3.client(
    's3',
    aws_access_key_id='AKIAJBUXGOYRGOGOMULA',
    aws_secret_access_key='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'
)

def lambda_handler(event, context):
    """
    Basic conversion of email file from s3 and upload extracted file attachment.
    :param event:
    :param context:
    :return:
    """
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.unquote_plus(event['Records'][0]['s3']['object']['key']).decode('utf8')
    try:
        email_obj = s3_client.get_object(Bucket=RESUMES_BUCKET, Key=key)
        email_file = email.message_from_string(email_obj['Body'].read())
        attachment = email_file.get_payload()[1]
        with open('/tmp/' + attachment.get_filename(), 'w') as outfile:
            outfile.write(attachment.get_payload())
            s3_client.upload_file('/tmp/' + attachment.get_filename(), 'resume-emails', attachment.get_filename())
    except Exception as e:
        print('Error getting object {} from bucket {}. {}.'.format(key, bucket, e))
        raise e

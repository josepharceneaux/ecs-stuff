import boto3
import argparse

SERVICE_NAME = 'service-name' # Service means getTalent micro service, not ECS service.
TAGS_ONLY = '--tags'
parser = argparse.ArgumentParser(description="Update and restart ECS tasks.")
parser.add_argument(SERVICE_NAME, nargs=1)
parser.add_argument(TAGS_ONLY, action='store_true')
args = parser.parse_args()
service = vars(args)[SERVICE_NAME][0]

tags_only = False
if args.tags:
    tags_only = True


ECS_CLIENT = boto3.client('ecr')


def validate_http_status(request_name, response):
    '''
    Validate that we got a good status on our request.

    :param request_name: Caller name to put in error message.
    :param response: The response to be validated.
    :return: None.
    '''
  
    try:
        http_status = response['ResponseMetadata']['HTTPStatusCode']
    except Exception as e:
        print "Exception getting HTTP status {}: {}".format(request_name, e.message)
        exit(1)

    if http_status != 200:
        print "Error with {}. HTTP Status: {}".format(request_name, http_status)
        exit(1)

def describe_image(image):
    if 'imageTag' in image:
        if tags_only:
            print "{}".format(image['imageTag'])
        else:
            print "{}:{}".format(image['imageDigest'], image['imageTag'])
    elif not tags_only:
        print "{}".format(image['imageDigest'])

service_path = "gettalent/" + service
response = ECS_CLIENT.list_images(repositoryName=service_path)
validate_http_status('list_images', response)

count = 0
while True:
    image_list = response['imageIds']

    for image in image_list:
        describe_image(image)
        count += 1

    if 'nextToken' not in response:
        break

    response = ECS_CLIENT.list_images(repositoryName=service_path, nextToken=response['nextToken'])
    validate_http_status('list_images', response)

print "{} images found.".format(count)

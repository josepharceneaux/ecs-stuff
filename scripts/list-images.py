import boto3
import argparse

import ecs_utils

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
ecs_utils.validate_http_status('list_images', response)

count = 0
while True:
    image_list = response['imageIds']

    for image in image_list:
        describe_image(image)
        count += 1

    if 'nextToken' not in response:
        break

    response = ECS_CLIENT.list_images(repositoryName=service_path, nextToken=response['nextToken'])
    ecs_utils.validate_http_status('list_images', response)

print "{} images found.".format(count)

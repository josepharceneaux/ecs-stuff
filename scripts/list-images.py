"""
List images in ECR repository.

Usage: python list-images.py <service-name> [ --tags none | --tags only ]

Optionally list images with no tags, list only images with tags, list all images.
"""

import boto3
import argparse

import ecs_utils


def describe_image(image):
    """
    Print information about an ECR image.

    :param json image: JSON description of image.
    """

    if 'imageTag' in image:
        print "{}:{}".format(image['imageDigest'], image['imageTag'])
    else:
        print "{}".format(image['imageDigest'])


SERVICE_NAME = 'service-name' # Service means getTalent micro service, not ECS service.
TAGS_ONLY = '--tags'
parser = argparse.ArgumentParser(description="List ECR images in repository.")
parser.add_argument(SERVICE_NAME, nargs=1)
parser.add_argument(TAGS_ONLY, choices=['only', 'none'])
args = parser.parse_args()
service = vars(args)[SERVICE_NAME][0]

tags_only = 'all'
if args.tags:
    tags_only = args.tags


ecr_client = ecs_utils.boto3.client('ecr')
image_list = ecs_utils.gather_images_from_repository(ecr_client, service, tags_only)

if tags_only == 'only':
    image_list = ecs_utils.sort_image_list_by_tag(image_list)

for image in image_list:
    describe_image(image)

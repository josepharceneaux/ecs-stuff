"""
Look for a service running on production and create a new task definition based upon that service's image
in staging, but with the tag we are passed.

Syntax: python move-stage-to-prod.py <service-name> <tag-name>

"""

import boto3
import argparse

import ecs_utils


def get_task_definition(client, td_name):
    """
    Get a task definition by name.

    :param obj client: The boto ECS client.
    :param str td_name: The name of the task description.
    """

    try:
        # This returns the latest ACTIVE revision
        task_definition = client.describe_task_definition(taskDefinition=td_name)
        ecs_utils.validate_http_status('get_task_description', task_definition)
    except Exception as e:
        print "Exception searching for task definition {}: {}".format(e.message, td_name)
        exit(1)

    return task_definition


def copy_stage_values_to_prod(service, source_td, destination_td, tag):
    """
    Copy the docker image from source to destination, and add a tag.

    :param str service: Name of the service we're updating.
    :param json source_td: The task description from which to copy the image.
    :param json destination_td: The task description in which to place the image.
    :param str tag: The docker tag to use on the image.
    """

    source_container_defs = source_td['taskDefinition']['containerDefinitions']
    destination_container_defs = destination_td['taskDefinition']['containerDefinitions']
    index = 0
    for source_definition in source_container_defs:
        source_image = source_definition['image']
        destination_definition = destination_container_defs[index]
        if tag:
            new_image = source_image.split(':')[0] + ':' + tag
        else:
            new_image = source_image

        if not ecs_utils.image_exists_in_repo(service, new_image):
            raise Exception("Can't find (in repo {}) image: {}".format(service, new_image))

        destination_definition['image'] = new_image
        index += 1


def update_prod_task_definition(client, family_name, definitions):
    """
    Create a new revision of a task definition.

    :param obj client: The boto ECS client.
    :param str family_name: The task name.
    :param json definitions: Container definitions (may only be one)
    """

    try:
        response = client.register_task_definition(family=family_name, containerDefinitions=definitions)
        ecs_utils.validate_http_status('update_prod_task_definition', response)
    except Exception as e:
        print "Exception {} registering task definition for {}".format(e.message, family_name)
        exit(1)

    td = response['taskDefinition']
    print "Task definition for {} updated to revision {}.".format(td['family'], td['revision'])
    return td['taskDefinitionArn']


# TODO: Use the generic version of this from ecs_utils
def update_service(client, prod_service_name, new_td_arn):
    """
    Update production service to use a new task definition revision.

    :param client obj: The boto client object.
    :param str prod_service_name: The getTalent service name.
    :param str new_td_arn: The AWS resource name for the task definition.
    """

    try:
        response = client.describe_services(cluster=ecs_utils.PROD_CLUSTER_NAME, services=[ prod_service_name ])
        ecs_utils.validate_http_status('describe_services', response)
    except Exception as e:
        print "Exception {} obtaining service description for {}".format(e.message, prod_service_name)
        exit(1)

    desired_count = response['services'][0]['desiredCount']
    deployment_configuration = response['services'][0]['deploymentConfiguration']
    try:
        response = client.update_service(cluster=ecs_utils.PROD_CLUSTER_NAME, service=prod_service_name, desiredCount=desired_count,
                                         taskDefinition=new_td_arn, deploymentConfiguration=deployment_configuration)
        ecs_utils.validate_http_status('update_service', response)
    except Exception as e:
        print "Exception {} updating service for {}".format(e.message, prod_service_name)
        exit(1)

    print "Successfully updated AWS service for {}".format(prod_service_name)


def migrate_stage_image_to_prod(service, tag):
    """
    Update production to use the docker image currently in staging.

    :param str service: The getTalent service name.
    :param str tag: The tag to be used (as in a version tag).
    """

    print "Migrating {} to production".format(service)

    # Service name
    stage_service_name = service + ecs_utils.STAGE_SVC_SUFFIX
    prod_service_name = service + ecs_utils.PROD_SVC_SUFFIX
    # Task description name
    stage_td_name = service + ecs_utils.STAGE_TD_SUFFIX
    prod_td_name = service + ecs_utils.PROD_TD_SUFFIX

    client = boto3.client('ecs')
    stage_td = get_task_definition(client, stage_td_name)
    prod_td = get_task_definition(client, prod_td_name)

    copy_stage_values_to_prod(service, stage_td, prod_td, tag)

    print "Stage: {}".format(stage_td['taskDefinition']['containerDefinitions'][0]['image'])
    print "Prod:  {}".format(prod_td['taskDefinition']['containerDefinitions'][0]['image'])

    new_td_arn = update_prod_task_definition(client, prod_td_name, prod_td['taskDefinition']['containerDefinitions'])
    # update the service and restart it
    update_service(client, prod_service_name, new_td_arn)


# Command line arguments
SERVICE_NAME = 'service-name' # Service means getTalent micro service, not ECS service.
TAG_NAME = '--tag'
parser = argparse.ArgumentParser(description="Restart production SERVICE with the image from staging, or that service with TAG, if provided.")
parser.add_argument(SERVICE_NAME, nargs=1)
parser.add_argument(TAG_NAME, nargs=1)
args = parser.parse_args()

service = vars(args)[SERVICE_NAME][0]
tag_name = None
if args.tag:
    tag_name = args.tag[0]
    print "{} {}".format(service, tag_name)
else:
    print service

migrate_stage_image_to_prod(service, tag_name)

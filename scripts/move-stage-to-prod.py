'''
Look for a service running on production and create a new task definition based upon that service
in staging, but with the tag we are passed.

Syntax: python move-stage-to-prod.py <service-name> <tag-name>

'''

import boto3
import argparse

def validate_http_status(request_name, response):
    '''
    Validate that we got a good status on our request.
    :param request_name: Caller name to put in error message.
    :param response: The response to be validated.
    '''
    
    try:
        http_status = response['ResponseMetadata']['HTTPStatusCode']
    except Exception as e:
        print "Exception getting HTTP status {}: {}".format(request_name, e.message)
        exit(1)

    if http_status != 200:
        print "Error with {}. HTTP Status: {}".format(request_name, http_status)
        exit(1)

def get_task_definition(client, td_name):
    '''
    Get a task definition by name.
    :param client: The boto ECS client.
    :td_name: The name of the task description.
    '''

    try:
        # This returns the latest ACTIVE revision
        task_definition = client.describe_task_definition(taskDefinition=td_name)
        validate_http_status('get_task_description', task_definition)
    except Exception as e:
        print "Exception {} searching for task definition {}".format(e.message, td_name)
        exit(1)

    return task_definition

def copy_stage_values_to_prod(source_td, destination_td, tag):
    '''
    Copy the docker image from source to destination, and add a tag.
    :param source_td: The task description from which to copy the image.
    :param destination_td: The task description in which to place the image.
    :param tag: The docker tag to use on the image.
    '''

    source_container_defs = source_td['taskDefinition']['containerDefinitions']
    destination_container_defs = destination_td['taskDefinition']['containerDefinitions']
    index = 0
    for source_definition in source_container_defs:
        source_image = source_definition['image']
        destination_definition = destination_container_defs[index]
        new_image = source_image.split(':')[0] + ':' + tag
        destination_definition['image'] = new_image
        index += 1

def migrate_stage_image_to_prod(service, tag):
    '''
    Update production to use the docker image currently in staging.
    :param service: The getTalent service name.
    :param tag: The tag to be used (as in a version tag).
    '''

    print "Migrating {} to production".format(service)
    # Service name
    stage_service_name = service + '-stage'
    prod_service_name = service + '-svc'
    # Task description name
    stage_td_name = service + '-stage-td'
    prod_td_name = service + '-td'
    # GT_ENVIRONMENT values
    stage_env = 'qa'
    prod_env = 'prod'

    client = boto3.client('ecs')
    stage_td = get_task_definition(client, stage_td_name)
    prod_td = get_task_definition(client, prod_td_name)

    print "Stage: {}:{} {}".format(stage_td['taskDefinition']['family'], stage_td['taskDefinition']['revision'], stage_td['taskDefinition']['status'])
    print "Prod: {}:{} {}".format(prod_td['taskDefinition']['family'], prod_td['taskDefinition']['revision'], prod_td['taskDefinition']['status'])

    copy_stage_values_to_prod(stage_td, prod_td, tag)
    print
    print "New Prod {}".format(prod_td['taskDefinition']['containerDefinitions'][0]['image'])
    # create new revision of prod task definition
    # update the service and restart it

# Command line arguments
SERVICE_NAME = 'service-name' # Service means getTalent micro service, not ECS service.
TAG_NAME = 'tag-name'
parser = argparse.ArgumentParser(description="Update and restart ECS tasks.")
parser.add_argument(SERVICE_NAME, nargs=1)
parser.add_argument(TAG_NAME, nargs=1)
args = parser.parse_args()
service = vars(args)[SERVICE_NAME][0]
tag = vars(args)[TAG_NAME][0]

migrate_stage_image_to_prod(service, tag)

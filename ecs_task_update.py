'''
Update an ECS task definition to point to a new docker image and potentially restart any services running the task.

Syntax: python ecs_task_update.py <service-name> <tag-name> [ stge | prod ] [ restart ]

This script is intended to be called from Jenkins. Tag is typically the build timestamp.
'''

import boto3
import argparse


def get_http_status(response):
    meta = response['ResponseMetadata']
    return meta['HTTPStatusCode']

def get_service_desired_count(response):
    return response['services'][0]['desiredCount']

def get_service_deployment(response):
    return response['services'][0]['deploymentConfiguration']

# Command line arguments
SERVICE_NAME = 'service-name' # Service means getTalent micro service, not ECS service.
TAG_NAME = 'tag-name'
CLUSTER_NAME = 'cluster-name'
RESTART_NAME = 'restart'

parser = argparse.ArgumentParser(description="Update and restart ECS tasks.")
parser.add_argument(SERVICE_NAME, nargs=1)
parser.add_argument(TAG_NAME, nargs=1)
parser.add_argument(CLUSTER_NAME, choices=['stage', 'prod'])
parser.add_argument(RESTART_NAME, nargs='?')
args = parser.parse_args()

service = vars(args)[SERVICE_NAME][0]
tag = vars(args)[TAG_NAME][0]
cluster = vars(args)[CLUSTER_NAME]
restart = args.restart

# Check our invocation and derive the AWS service and task definition names from the getTalent service name
if cluster == 'stage':
    service_svc = service + "-stage"
    gt_environment = 'qa'
    service_td = service + '-stage-td'
else:
    service_svc = service + "-svc"
    gt_environment = 'prod'
    service_td = service + '-td'


# Perhaps validate that this service is among those currently running? Have to figure out naming problem.


client = boto3.client('ecs')
try:
    # This returns the latest ACTIVE revision
    task_definition = client.describe_task_definition(taskDefinition=service_td)
    if get_http_status(task_definition) != 200:
        print "Error Fetching Task Description. HTTP Status: {}".format(get_http_status(response))
        exit(1)
except Exception as e:
    print "Exception {} searching for task definition {}".format(e.message, service)
    exit(1)


# We are running single container tasks for the moment, but we may change that
print "Processing {} containers for service {}".format(len(task_definition['taskDefinition']['containerDefinitions']), service_svc)
for definition in task_definition['taskDefinition']['containerDefinitions']:
    image = definition['image']
    # Create a new image pointer with our new tag
    new_image = image.split(':')[0] + ':' + tag
    definition['image'] = new_image
    name = [ v for v in definition['environment'] if v['name'] == 'GT_ENVIRONMENT' ]
    name[0]['value'] = gt_environment

for definition in task_definition['taskDefinition']['containerDefinitions']:
    print "Updated container image with: {}".format(definition['image'])

# Create a new revision of the task definition
try:
    response = client.register_task_definition(family=service_td, containerDefinitions=task_definition['taskDefinition']['containerDefinitions'])
    if get_http_status(response) != 200:
        print "Error Registering Task Definition. HTTP Status: {}".format(get_http_status(response))
        exit(1)
except Exception as e:
    print "Exception {} registering task definition for {}".format(e.message, service_svc)
    exit(1)


td = response['taskDefinition']
new_td_arn = td['taskDefinitionArn']
print "Task definition for {} updated to revision {}.".format(td['family'], td['revision'])


# Conditionally restart the tasks
if restart == 'restart':
    try:
        response = client.describe_services(cluster=cluster, services=[ service_svc ])
        if get_http_status(response) != 200:
            print "Error Fetching Service {} in cluster {}, HTTP Status: {}".format(service_svc, cluster, get_http_status(response))
            exit(1)
    except Exception as e:
        print "Exception {} searching for service description {} in cluster {}".format(e.message, service_svc, cluster)
        exit(1)

    try:
        print "Updating AWS service {} in {} cluster, desired_count = {}".format(service_svc, cluster, get_service_desired_count(response))
        response = client.update_service(cluster=cluster, service=service_svc, desiredCount=get_service_desired_count(response),
                                         taskDefinition=new_td_arn, deploymentConfiguration=get_service_deployment(response))
        if get_http_status(response) != 200:
            print "Error Updating Service. HTTP Status: {}".format(get_http_status(response))
            exit(1)
    except Exception as e:
        print "Exception {} updating service {}".format(e.message, service_svc)
        exit(1)

    print "Successfully updated AWS service for {}".format(service_svc)

# Consider garbage collecting Task Definitions?

exit(0)

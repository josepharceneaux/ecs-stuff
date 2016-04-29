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
cluster = vars(args)[CLUSTER_NAME][0]
restart = args.restart

# Check our invocation and derive the AWS service and task definition names from the getTalent service name
if cluster != 'stage' and cluster != 'prod':
    print "Bad cluster name: {}".format(cluster)
if cluster == 'stage':
    service_svc = service
else:
    service_svc = service + "-svc"
service_svc = service + '-svc'
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
print "Processing {} containers for service {}".format(len(task_definition['taskDefinition']['containerDefinitions']), service)
for definition in task_definition['taskDefinition']['containerDefinitions']:
    image = definition['image']
    # Create a new image pointer with our new tag
    new_image = image.split(':')[0] + ':' + tag
    definition['image'] = new_image

for definition in task_definition['taskDefinition']['containerDefinitions']:
    print "Updated container image with: %s" % definition['image']

# Create a new revision of the task definition
try:
    response = client.register_task_definition(family=service_td, containerDefinitions=task_definition['taskDefinition']['containerDefinitions'])
    if get_http_status(response) != 200:
        print "Error Registering Task Definition. HTTP Status: {}".format(get_http_status(response))
        exit(1)
except Exception as e:
    print "Exception {} registering task definition for {}".format(e.message, service)
    exit(1)

print "Task definition %s updated." % service


# Conditionally restart the tasks
if restart == 'restart':
    print "Updating service and restarting tasks"
    response = client.describe_services(cluster=cluster, services=[ service_svc ])
    if get_http_status(response) != 200:
        print "Error Fetching Service. HTTP Status: {}".format(get_http_status(response))
        exit(1)

    response = client.update_service(cluster=cluster, service=service_svc, desiredCount=get_service_desired_count(response),
                                     taskDefinition=task_definition['taskDefinition'], deploymentConfiguration=get_service_deployment(response))


# Consider garbage collecting Task Definitions?

exit(0)

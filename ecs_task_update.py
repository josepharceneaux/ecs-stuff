import boto3
import argparse
import json


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
print "RESTART: {}".format(restart)

# Adjust for our ECS naming convention. Really should not do it this way.
service += '-td'

client = boto3.client('ecs')

try:
    # This returns the latest ACTIVE revision
    task_definition = client.describe_task_definition(taskDefinition=service)
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

# Now create a new revision of the task definition
try:
    response = client.register_task_definition(family=service, containerDefinitions=task_definition['taskDefinition']['containerDefinitions'])
except Exception as e:
    print "Exception {} registering task definition for {}".format(e.message, service)
    exit(1)

print "Task definition %s updated." % service

# Conditionally restart the tasks
if restart == 'restart':
    print "Restarting tasks"
    # Do we need to wait before starting again?
    # We could specify the container instance, or let the ECS scheduler do it

# Consider garbage collecting Task Definitions?

exit(0)

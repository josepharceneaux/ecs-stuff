import boto3
import argparse
import json


# Command line arguments
SERVICE_NAME = 'service-name'
TAG_NAME = 'tag-name'

parser = argparse.ArgumentParser(description="Update and restart ECS tasks.")
parser.add_argument(SERVICE_NAME, nargs=1)
parser.add_argument(TAG_NAME, nargs=1)
args = parser.parse_args()

service = vars(args)[SERVICE_NAME][0]
tag = vars(args)[TAG_NAME][0]
service += '-td' # Adjust for our ECS naming convention

client = boto3.client('ecs')

try:
    # This returns the latest ACTIVE revision
    task_definition = client.describe_task_definition(taskDefinition=service)
except Exception as e:
    print "Exception {} searching for task definition {}".format(e.message, service)
    exit(1)

# We are running single container tasks
if len(task_definition['taskDefinition']['containerDefinitions'][0]):
    print "EXCEPTION: More than 1 container definition for %s" % service
    exit(1)

image = task_definition['taskDefinition']['containerDefinitions'][0]['image']

# Get the image without the tag and create new image with our new tag
new_image = image.split(':')[0] + ':' + tag

print "Creating new task definition with image: %s" % new_image
task_definition['taskDefinition']['containerDefinitions'][0]['image'] = new_image

try:
    response = client.register_task_definition(family=service, containerDefinitions=task_definition['taskDefinition']['containerDefinitions'])
except Exception as e:
    print "Exception {} registering task definition for {}".format(e.message, service)
    exit(1)

# Consider garbage collecting Task Definitions?

print "Updated: %s" % task_definition['taskDefinition']['containerDefinitions'][0]['image']
exit(0)

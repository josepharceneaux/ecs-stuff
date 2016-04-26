import boto3
import argparse

SERVICE_NAME = 'service-name'
TAG_NAME = 'tag-name'

parser = argparse.ArgumentParser(description="Update and restart ECS tasks.")
parser.add_argument(SERVICE_NAME, nargs=1)
parser.add_argument(TAG_NAME, nargs=1)
args = parser.parse_args()

service = vars(args)[SERVICE_NAME][0]
tag = vars(args)[TAG_NAME][0]

print "Service: %s" % service
print "Tag: %s" % tag

client = boto3.client('ecs')
print "Client: %s" % client

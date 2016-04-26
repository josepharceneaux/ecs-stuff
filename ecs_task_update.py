import boto3

client = boto3.client('ecs')

print "Client: %s" % client

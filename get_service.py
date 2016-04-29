import boto3
import argparse

# Command line arguments
SERVICE_NAME = 'service-name' # Service means getTalent micro service, not ECS service.
parser = argparse.ArgumentParser(description="Examine ECS service.")
parser.add_argument(SERVICE_NAME, nargs=1)
args = parser.parse_args()
service = vars(args)[SERVICE_NAME][0]


def get_http_status(response):
    meta = response['ResponseMetadata']
    return meta['HTTPStatusCode']

def get_service_desired_count(response):
    return response['services'][0]['desiredCount']

def get_service_max_percent(response):
    return response['services'][0]['deploymentConfiguration']['maximumPercent']

def get_service_min_percent(response):
    return response['services'][0]['deploymentConfiguration']['minimumHealthyPercent']

def get_service_deployment(response):
    return response['services'][0]['deploymentConfiguration']

# Check our invocation
cluster='stage'
service_td = service + "-td"
if cluster == 'stage':
    service_svc = service
else:
    service_svc = service + "-svc"

client = boto3.client('ecs')
print "Retrieving service description for {}".format(service_svc)
response = client.describe_services(cluster=cluster, services=[ service_svc ])
if get_http_status(response) != 200:
    print "Describe Services Status: {}".format(get_http_status(response))
    exit(1)

print "Desired Count: {}".format(get_service_desired_count(response))
print "Deployment: {}".format(get_service_deployment(response))
print "Min Percentage: {}".format(get_service_min_percent(response))
print "Max Percentage: {}".format(get_service_max_percent(response))

task_definition = client.describe_task_definition(taskDefinition=service_td)
if get_http_status(task_definition) != 200:
    print "Describe Task Status: {}".format(get_http_status(response))
    exit(1)

print "Got task definition."

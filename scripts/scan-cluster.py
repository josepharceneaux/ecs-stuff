'''
Scan an AWS ECS cluster and list the services (and their task definitions) currently running.

Syntax: python scan-cluster.py [ stage | prod ]

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

def scan_cluster(cluster):
    if cluster == 'stage':
        print "STAGING"
    else:
        print "PRODUCTION"
    print

    client = boto3.client('ecs')
    services_response = client.list_services(cluster=cluster)
    validate_http_status('list_tasks', services_response)
    service_list = services_response['serviceArns']

    count = 0
    while True:
        for service in service_list:
            print
            response = client.describe_services(cluster=cluster, services=[ service ])
            validate_http_status('describe_services', response)
            print "{} Services. First: Name: {} Status: {} Deployments: {}".format(len(response['services']), response['services'][0]['serviceName'],
                                                                                   response['services'][0]['status'], len(response['services'][0]['deployments']))
            td = response['services'][0]['taskDefinition']
            # print "Task Definition: {}".format(td)
            response = client.describe_task_definition(taskDefinition=td)
            validate_http_status('describe_services', response)
            print "TD - Family: {} Revision: {} Status: {}".format(response['taskDefinition']['family'],
                                                                   response['taskDefinition']['revision'],
                                                                   response['taskDefinition']['status'])
            count += 1

        if 'nextToken' not in services_response:
            break

        services_response = client.list_services(cluster=cluster, nextToken=services_response['nextToken'])
        validate_http_status('list_tasks', services_response)
        service_list = services_response['serviceArns']

    print "{} services found.".format(count)


CLUSTER_NAME = 'cluster-name'
parser = argparse.ArgumentParser(description="Update and restart ECS tasks.")
parser.add_argument(CLUSTER_NAME, choices=['stage', 'prod'])
args = parser.parse_args()
cluster = vars(args)[CLUSTER_NAME]

scan_cluster(cluster)

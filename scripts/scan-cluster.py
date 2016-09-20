'''
Scan an AWS ECS cluster and list the services (and their task definitions) currently running.

Syntax: python scan-cluster.py [ stage | prod ]

'''

import boto3
import argparse

from ecs_utils import validate_http_status, gather_task_definitions #, gt_service_name_from_arn


def describe_service(cluster, service_arn):
    '''
    Describe an ECS service and its task definition

    :param cluster: The cluster to inspect.
    :param service_arn: The service to describe.
    :return: None.
    '''

    print
    response = ECS_CLIENT.describe_services(cluster=cluster, services=[ service_arn ])
    validate_http_status('describe_services', response)
    print "{} {} Deployments: {}".format(response['services'][0]['serviceName'],
                                         response['services'][0]['status'],
                                         len(response['services'][0]['deployments']))

    td = response['services'][0]['taskDefinition']
    response = ECS_CLIENT.describe_task_definition(taskDefinition=td)
    validate_http_status('describe_services', response)
    print "Task: Family: {} Revision: {} Status: {}".format(response['taskDefinition']['family'],
                                                            response['taskDefinition']['revision'],
                                                            response['taskDefinition']['status'])
    # TODO: Add this line
    # print "Available Task Revsions: {} - {}".format(first_revision, last_revision)
    print "Image: {}".format(response['taskDefinition']['containerDefinitions'][0]['image'])
    print "CPU: {} Memory {}: ".format(response['taskDefinition']['containerDefinitions'][0]['cpu'], response['taskDefinition']['containerDefinitions'][0]['memory'])

def scan_cluster(cluster):
    '''
    Scan an ECS cluster and describe its services and task definitions.

    :param cluster: The cluster to inspect.
    :return: None.
    '''

    services_response = ECS_CLIENT.list_services(cluster=cluster)
    validate_http_status('list_tasks', services_response)

    count = 0
    while True:
        service_list = services_response['serviceArns']

        for service in service_list:
            describe_service(cluster, service)
            count += 1

        if 'nextToken' not in services_response:
            break

        services_response = ECS_CLIENT.list_services(cluster=cluster, nextToken=services_response['nextToken'])
        validate_http_status('list_tasks', services_response)

    print
    print "{} services found.".format(count)


CLUSTER_NAME = 'cluster-name'
ECS_CLIENT = boto3.client('ecs')

parser = argparse.ArgumentParser(description="Update and restart ECS tasks.")
parser.add_argument(CLUSTER_NAME, choices=['stage', 'prod'])
args = parser.parse_args()
cluster = vars(args)[CLUSTER_NAME]

scan_cluster(cluster)

"""
"""


import boto3
import argparse

from ecs_utils import get_all_services, update_service_task_definition, fatal


# Arguments
CLUSTER_NAME = 'cluster-name'
SERVICE_NAME = 'service-name'
ADJUSTMENT = 'adjustment'
# Name to use for service if we want to change all of them
ALL_SERVICES = 'all-services'

ECS_CLIENT = boto3.client('ecs')

parser = argparse.ArgumentParser(description="Change ECS task definition and restart service.")
parser.add_argument(CLUSTER_NAME, choices=['stage', 'prod'])
parser.add_argument(SERVICE_NAME)
parser.add_argument(ADJUSTMENT)
args = parser.parse_args()
cluster = vars(args)[CLUSTER_NAME]
service = vars(args)[SERVICE_NAME]
adjustment = vars(args)[ADJUSTMENT]

print "{} {} {}".format(cluster, service, adjustment)

# Validate adjustment
if adjustment[0] != '-' and adjustment[0] != '+':
    fatal("Adjustment must begin with + or -")
amount = adjustment[1:(len(adjustment))]
if not amount.isdigit():
    fatal("Adjustment must be a decimal number beginning with + or -")

if service == ALL_SERVICES:
    print "Changing all services on {} cluster...".format(cluster)
    # Gather all service names in cluster into a list
    service_list = get_all_services(ECS_CLIENT, cluster)

    # Change each service
    error_count = 0
    for service_name in service_list:
        print service_name
        # Update service
        if not update_service_task_definition(ECS_CLIENT, cluster, service_name, adjustment):
            error_count += 1

    if error_count > 0:
        print "{} failures.".format(error_count)
    else:
        print "Done."
else:
    print "Changing service {} on {} cluster...".format(service, cluster)
    if update_service_task_definition(ECS_CLIENT, cluster, service, adjustment):
        print "Done."
    else:
        print "Failed."

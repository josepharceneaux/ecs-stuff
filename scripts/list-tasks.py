import boto3
import argparse

import ecs_utils

CLUSTER_NAME = 'cluster-name'
SERVICE_NAME = 'service-name' # Service means getTalent micro service, not ECS service.
parser = argparse.ArgumentParser(description="Update and restart ECS tasks.")
parser.add_argument(SERVICE_NAME, nargs=1)
parser.add_argument(CLUSTER_NAME, choices=['stage', 'prod'])
args = parser.parse_args()
cluster = vars(args)[CLUSTER_NAME]
service = vars(args)[SERVICE_NAME][0]

# ecs_utils.gather_task_definitions(service, cluster)
ecs_utils.garbage_collect_ecs(service, cluster)

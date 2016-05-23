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
# ecs_utils.garbage_collect_ecs(service, cluster)


ecs_client = boto3.client('ecs')

ecs_utils.delete_images_from_repository(ecs_client, '528222547498.dkr.ecr.us-east-1.amazonaws.com/gettalent/candidate-service:built-at-2016-05-04-14-52-52', 'candidate-service')

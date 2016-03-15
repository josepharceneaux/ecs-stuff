#!/bin/bash

eval $(aws ecr get-login --region us-east-1)

FLASK_APPS=("auth-service" "activity-service" "resume-parsing-service" "user-service" "candidate-service" "social-network-service" "candidate-pool-service" "spreadsheet-import-service" "scheduler-service" "sms-campaign-service" "push-campaign-service" "email-campaign-service")

ecr_registry_url="528222547498.dkr.ecr.us-east-1.amazonaws.com"

for app_index in ${!FLASK_APPS[@]}

do
    tag_command="docker tag -f gettalent/${FLASK_APPS[$app_index]}:latest ${ecr_registry_url}/gettalent/${FLASK_APPS[$app_index]}:latest"
    echo $tag_command
    eval $tag_command
    push_command="docker push ${ecr_registry_url}/gettalent/${FLASK_APPS[$app_index]}:latest"
    echo $push_command
    eval $push_command
done
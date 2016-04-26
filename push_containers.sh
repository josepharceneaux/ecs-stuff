#!/bin/bash

# Push containers built by Jenkins to either staging or production

eval $(aws ecr get-login --region us-east-1)

FLASK_APPS=("auth-service" "activity-service" "resume-parsing-service" "user-service" "candidate-service" "social-network-service" "candidate-pool-service" "spreadsheet-import-service" "scheduler-service" "sms-campaign-service" "push-campaign-service" "email-campaign-service")

ecr_registry_url="528222547498.dkr.ecr.us-east-1.amazonaws.com"

# Only push to production if explicitly specified
if [[ $1 && $1 == "prod" ]] ; then
    production="true"
fi

# Consider error if branch is master and production was specified

timestamp=`date +"%Y-%m-%d-%H-%M-%S"`
timestamp_tag="built-at-$timestamp"
echo "Using tag ${timestamp_tag}"
git --version

for app_index in ${!FLASK_APPS[@]}

do
    if [ $production ] ; then
	tag_command="docker tag -f gettalent/${FLASK_APPS[$app_index]}:latest ${ecr_registry_url}/gettalent/${FLASK_APPS[$app_index]}:latest"
	echo $tag_command
        eval $tag_command
	push_command="docker push ${ecr_registry_url}/gettalent/${FLASK_APPS[$app_index]}:latest"
	echo $push_command
        eval $push_command
    else
	tag_command="docker tag -f gettalent/${FLASK_APPS[$app_index]}:${timestamp_tag} ${ecr_registry_url}/gettalent-stage/${FLASK_APPS[$app_index]}:${timestamp_tag}"
	echo $tag_command
        eval $tag_command

	push_command="docker push ${ecr_registry_url}/gettalent-stage/${FLASK_APPS[$app_index]}:${timestamp_tag}"
	echo $push_command
        eval $push_command

	# Update task definition for this service
    fi
done

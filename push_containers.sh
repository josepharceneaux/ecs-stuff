#!/bin/bash

# Push containers built by Jenkins to either staging or production
echo "Pushing containers"

eval $(aws ecr get-login --region us-east-1)

# Skipping push-campaign-service
FLASK_APPS="auth-service activity-service resume-parsing-service user-service candidate-service social-network-service candidate-pool-service spreadsheet-import-service scheduler-service sms-campaign-service email-campaign-service"

ecr_registry_url="528222547498.dkr.ecr.us-east-1.amazonaws.com"

# Only push to production if explicitly specified
if [[ $1 && $1 == "prod" ]] ; then
    production="true"
fi

# Consider error if branch is master and production was specified

# Consider handling docker errors - just exit?

timestamp=`date +"%Y-%m-%d-%H-%M-%S"`
timestamp_tag="built-at-$timestamp"

# for app_index in ${FLASK_APPS}
for app in ${FLASK_APPS}

do
    tag_command="docker tag -f gettalent/${app} ${ecr_registry_url}/gettalent/${app}:${timestamp_tag}"
    echo $tag_command
    eval $tag_command

    push_command="docker push ${ecr_registry_url}/gettalent/${app}:${timestamp_tag}"
    echo $push_command
    eval $push_command

    if [ $production ] ; then
	# Update task definition for this service
	# python ecs_task_update.py ${app} ${timestamp_tag} prod
	echo "Not yet pushing to production - THIS SHOULDN'T BE HERE"
    else
	# Update task definition for this service and restart staging services
	echo "python ecs_task_update.py ${app} ${timestamp_tag} stage restart"
	python ecs_task_update.py ${app} ${timestamp_tag} stage restart
    fi
done

# If we've pushed and tagged all the images, tag the branch
echo "Tagging branch with ${timestamp_tag}"

# Need to turn off triggering from tag push..?
# git tag -a ${timestamp_tag} -m "Adding timestamp tag"
# This triggers another build. Have to figure out how to recognize it.
# git push origin ${timestamp_tag}

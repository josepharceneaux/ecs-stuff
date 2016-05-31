#!/bin/bash

# Push containers built by Jenkins to either staging or production
echo "Pushing containers"

eval "$(aws ecr get-login --region us-east-1)"

FLASK_APPS="auth-service activity-service resume-parsing-service user-service candidate-service social-network-service candidate-pool-service spreadsheet-import-service scheduler-service sms-campaign-service push-campaign-service email-campaign-service"

ecr_registry_url="528222547498.dkr.ecr.us-east-1.amazonaws.com"

# Only push to production if explicitly specified
if [[ $1 && $1 == "prod" ]] ; then
    production="true"
fi

if [ $production ] ; then
    version_tag=`git tag --points-at HEAD | grep '^v.\+' `

    if [ ! $version_tag ] ; then
	echo "No version tag points to HEAD"
	exit 1
    fi

    for app in ${FLASK_APPS}
    do
	# Pull the image staging is using
	stage_image=`python scripts/scan-cluster.py stage | grep ${app} | grep Image | awk '{ print $NF }'`
	pull_command="docker pull ${stage_image}"
	echo $pull_command
	eval $pull_command
	if [ $? -ne 0 ] ; then
	    continue
	fi

	# Tag it with the version
	tag_command="docker tag -f ${stage_image} ${ecr_registry_url}/gettalent/${app}:${version_tag}"
	echo $tag_command
	eval $tag_command
	if [ $? -ne 0 ] ; then
	    continue
	fi

	# Push it back to the repo
	push_command="docker push ${ecr_registry_url}/gettalent/${app}:${version_tag}"
	echo $push_command
	eval $push_command
	if [ $? -ne 0 ] ; then
	    continue
	fi

	# Update the task definition and restart the service
	move_command="python scripts/move-stage-to-prod.py ${app} --tag ${version_tag}"
	echo $move_command
	eval $move_command
    done

else
    timestamp=`date +"%Y-%m-%d-%H-%M-%S"`
    timestamp_tag="built-at-$timestamp"

    for app in ${FLASK_APPS}
    do
	# Tag the image with a timestamp
	tag_command="docker tag -f gettalent/${app} ${ecr_registry_url}/gettalent/${app}:${timestamp_tag}"
	echo $tag_command
        eval $tag_command
	if [ $? -ne 0 ] ; then
	    continue
	fi

	# Push the image to our repository
	push_command="docker push ${ecr_registry_url}/gettalent/${app}:${timestamp_tag}"
	echo $push_command
        eval $push_command
	if [ $? -ne 0 ] ; then
	    continue
	fi

	# Update task definition for this service and restart staging services
	move_command="python ecs_task_update.py ${app} ${timestamp_tag} stage restart"
	echo $move_command
	eval $move_command
    done

    # If we've pushed and tagged all the images, tag the branch
    echo "Tagging branch with ${timestamp_tag}"
    git tag -a ${timestamp_tag} -m "Adding timestamp tag"
    git push origin ${timestamp_tag}

fi

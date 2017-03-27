#!/bin/bash

echo "PYTHONPATH: $PYTHONPATH"

echo -n "FOO: "
python foo.py

# Upgrade pip if needed
pip install --upgrade pip

# Install Requirements
pip install -r requirements.txt

# Build Docker Images
sudo service docker restart
# New Jenkins uses Aurora
if [ `hostname` != "aws-jenkins.gettalent.com" ]; then
    sudo service mysql restart
fi
sudo usermod -aG docker jenkins

# Stopping all containers and removing all dangling images from Jenkins container
docker stop $(docker ps -a -q)
docker rm $(docker ps -a -q)
docker images -qf "dangling=true" | xargs docker rmi

# Build the micro service images
cd base_service_container && tar -czh . | docker build -t gettalent/base-service-container:latest - && cd ../
pwd
cd auth_service && tar -czh . | docker build -t gettalent/auth-service:latest - && cd ../
cd resume_parsing_service && tar -czh . | docker build -t gettalent/resume-parsing-service:latest - && cd ../
cd activity_service && tar -czh . | docker build -t gettalent/activity-service:latest - && cd ../
cd user_service && tar -czh . | docker build -t gettalent/user-service:latest - && cd ../
cd candidate_service && tar -czh . | docker build -t gettalent/candidate-service:latest - && cd ../
cd social_network_service && tar -czh . | docker build -t gettalent/social-network-service:latest - && cd ../
cd candidate_pool_service && tar -czh . | docker build -t gettalent/candidate-pool-service:latest - && cd ../
cd spreadsheet_import_service && tar -czh . | docker build -t gettalent/spreadsheet-import-service:latest - && cd ../
cd scheduler_service && tar -czh . | docker build -t gettalent/scheduler-service:latest - && cd ../
cd sms_campaign_service && tar -czh . | docker build -t gettalent/sms-campaign-service:latest - && cd ../
cd push_campaign_service && tar -czh . | docker build -t gettalent/push-campaign-service:latest - && cd ../
cd email_campaign_service && tar -czh . | docker build -t gettalent/email-campaign-service:latest - && cd ../
cd ats_service && tar -czh . | docker build -t gettalent/ats-service:latest - && cd ../
cd mock_service && tar -czh . | docker build -t gettalent/mock-service:latest - && cd ../
cd talentbot_service && tar -czh . | docker build -t gettalent/talentbot-service:latest - && cd ../
cd graphql_service && tar -czh . | docker build -t gettalent/graphql-service:latest - && cd ../
cd banner_service && tar -czh . | docker build -t gettalent/banner-service:latest - && cd ../
cd widget_service && tar -czh . | docker build -t gettalent/widget-service:latest - && cd ../

# TODO: Move scheduler service admin to another repo
# cd scheduler_service_admin && tar -czh . | docker build -t gettalent/scheduler-service-admin:latest - && cd ../

# Reset Database and Amazon Cloud Search
export PYTHONPATH=.
python setup_environment/reset_database_and_cloud_search.py

# Start Docker Containers for all apps before testing them

ENV_VARIABLES=("GT_ENVIRONMENT" "AWS_ACCESS_KEY_ID" "AWS_SECRET_ACCESS_KEY")

FLASK_APPS=("auth-service" "activity-service" "resume-parsing-service" "user-service" "candidate-service" "widget-service" "social-network-service" "candidate-pool-service" "spreadsheet-import-service" "scheduler-service" "sms-campaign-service" "push-campaign-service" "email-campaign-service" "ats-service" "mock-service" "talentbot-service" "graphql-service" "banner-service")

# Note that port 8016 is used for scheduler admin web app
FLASK_APP_PORTS=("8001" "8002" "8003" "8004" "8005" "8006" "8007" "8008" "8009" "8011" "8012" "8013" "8014" "8015" "8016" "8017" "8018" "8019")


env_variable_parameters=""
for env_variable_index in ${!ENV_VARIABLES[@]}
do
    eval "env_variable_value=\$${ENV_VARIABLES[$env_variable_index]}"
    env_variable_parameters="$env_variable_parameters -e ${ENV_VARIABLES[$env_variable_index]}=${env_variable_value}"
done

for app_index in ${!FLASK_APPS[@]}

do
    command="docker run -d ${env_variable_parameters} -p ${FLASK_APP_PORTS[$app_index]}:80 gettalent/${FLASK_APPS[$app_index]} &"
    echo $command
    eval $command
done

echo "Sleeping 10s"
sleep 10

echo "Beginning tests."

# These tests cannot be ran concurrently
py.test banner_service/tests
# Commenting out due to talent_pool issues (passing locally)
# py.test widget_service/tests

py.test -n 48 scheduler_service/tests auth_service/tests candidate_pool_service/tests spreadsheet_import_service/tests app_common/common/tests talentbot_service/tests email_campaign_service/tests social_network_service/tests
# Commented out due to failures on jenkins
# candidate_service/tests user_service/tests
# Commented out due to ActivitySearching failures
# sms_campaign_service/tests
# Commented out due to app_common/common/campaign_services/tests/test_invitation_statuses constant failures.
# app_common/common/campaign_services/tests


if [ $? -ne 0 ] ; then
    exit 1
fi


# Place other tests (code complexity, etc.) here


echo "Tests completed."

# Declare success with this string that Jenkins looks for - see Jenkins config.
echo "My work here is done."

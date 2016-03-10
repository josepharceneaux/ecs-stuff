#!/bin/bash

# Install Requirements
pip install -r requirements.txt

# Build Docker Images
sudo service docker restart
sudo usermod -aG docker jenkins

# Sopping all containers and removing all dangling images from Jenkins container
docker stop $(docker ps -a -q)
docker rm $(docker ps -a -q)
docker images -qf dangling=true | xargs docker rmi

cd base_service_container && tar -czh . | docker build -t gettalent/base-service-container:latest - && cd ../
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

# Reset Database and Amazon Cloud Search
export PYTHONPATH=.
python setup_environment/reset_database_and_cloud_search.py
# Running Docker Containers for all apps before testing them

ENV_VARIABLES=("GT_ENVIRONMENT" "AWS_ACCESS_KEY_ID" "AWS_SECRET_ACCESS_KEY")

FLASK_APPS=("auth-service" "activity-service" "resume-parsing-service" "user-service" "candidate-service" "social-network-service" "candidate-pool-service" "spreadsheet-import-service" "scheduler-service" "sms-campaign-service" "push-campaign-service" "email-campaign-service")

FLASK_APP_PORTS=("8001" "8002" "8003" "8004" "8005" "8007" "8008" "8009" "8011" "8012" "8013" "8014")

output=""

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

sleep 10

py.test -n 16 scheduler_service/tests/ auth_service/tests/ user_service/tests activity_service/tests/ resume_parsing_service/tests candidate_pool_service/tests/ candidate_service/tests spreadsheet_import_service/tests/ email_campaign_service/tests push_campaign_service/tests

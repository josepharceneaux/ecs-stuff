__author__ = 'erikfarmer'


import argparse
import os
from subprocess import call, check_output
from sys import exit, platform as _platform

VM_NOT_RUNNING_ERROR_MESSAGE = 'Virtual Machine is not running. Please start it with docker-machine start VM_NAME'
SERVICES = ['activity_service', 'auth_service', 'candidate_service', 'resume_service']
SERVICE_TO_DOCKERHUB_REPO = {'activity_service': 'activities-service',
                             'auth_service': 'authservice',
                             'resume_service': 'resume-parsing-service',
                             'candidate_service': 'candidate-service'}

parser = argparse.ArgumentParser(description='Common files administrator for Docker building.')
parser.add_argument('--build', nargs=1, choices=SERVICES, help='Invokes the Docker build action for given service')
args = parser.parse_args()


def set_environment_variables_from_env_output(env_output=''):
    print env_output
    # We ignore env variables that start with DOCKER_, those are Docker ones
    env_output_lines = filter(None,
                              filter(lambda line: not line.startswith(("DOCKER_", "#")),
                                     env_output.split('\n')))
    # print 'output lines %s' % env_output_lines
    for variable in env_output_lines:
        environment_variable_name_value = variable.strip('export').strip().split('=')
        if len(environment_variable_name_value) == 2:
            os.environ[environment_variable_name_value[0]] = environment_variable_name_value[1].strip('"')
        else:
            exit(VM_NOT_RUNNING_ERROR_MESSAGE)

if args.build:
    service_name = args.build[0]

    # If on OS X, use docker-machine to run Docker client
    repo_name = "gettalent/%s" % SERVICE_TO_DOCKERHUB_REPO[service_name]
    os.chdir(service_name)

    if _platform == "darwin" or _platform == "win32":  # Host machine is not linux based
        print 'OS X or Windows detected. Attaching bash shell to Virtual Machine'

        # Configure Docker env for this process
        try:
            check_output('eval "$(docker-machine env default)"', shell=True)
        except Exception as e:
            exit(e.message)

        # Set the environment variables from the Docker env
        try:
            command = 'docker-machine env default'
            print command
            set_environment_variables_from_env_output(check_output(command, shell=True))
        except Exception as e:
            exit(e.message)

    # Build Dockerfile & push to DockerHub
    print 'Building Docker file for service %(service_name)s, repo %(repo_name)s:' % locals()
    command = 'tar -czh . | docker build -t %(repo_name)s:latest -' % locals()
    print command
    call(command, shell=True)

    print 'Pushing %(repo_name)s:latest to docker-hub registry' % locals()
    command = 'docker push %(repo_name)s:latest' % locals()
    print command
    call(command, shell=True)

    # TODO: Running and testing docker container locally

    # Deploy to webdev via Ansible
    print 'Deploying docker container to staging'
    os.chdir('../ansible-deploy')
    command = 'ansible-playbook -i hosts --extra-vars "host=staging" --extra-vars ' \
              '"service=%s" ansible-deploy.yml' % SERVICE_TO_DOCKERHUB_REPO[service_name]
    print command
    call(command, shell=True)

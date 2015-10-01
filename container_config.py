__author__ = 'erikfarmer'


import argparse
import os
from subprocess import call, check_output
from sys import exit, platform as _platform

virtual_machine_error_message = 'Virtual Machine is not running. Please start it with docker-machine start VM_NAME'
services = ['auth_service', 'candidate_service', 'resume_service']
service_name_to_repo = {'auth_service': 'authservice',
                        'resume_service': 'resume-parsing-service',
                        'candidate_service': 'candidate-service'}

parser = argparse.ArgumentParser(description='Common files administrator for Docker building.')
parser.add_argument('--build', nargs=1, choices=services, help='Invokes the Docker build action for given service')
args = parser.parse_args()


def set_environment(variables=''):
    variables = variables.split('\n')
    if variables and len(variables) >= 4:
        variables = variables[:4]
        for variable in variables:
            environment_variable = variable.strip('export').strip().split('=')
            if len(environment_variable) == 2:
                os.environ[environment_variable[0]] = environment_variable[1].strip('"')
            else:
                exit(virtual_machine_error_message)
    else:
        exit(virtual_machine_error_message)

if args.build:
    service_name = args.build[0]
    repo_name = "gettalent/%s" % service_name_to_repo[service_name]
    os.chdir(service_name)

    if _platform == "darwin" or _platform == "win32":  # Host machine is not linux based
        print 'Attaching bash shell to Virtual Machine'
        command = 'docker-machine env default'
        print 'Command: ' + command

        try:
            set_environment(check_output('docker-machine env default', shell=True))
        except Exception as e:
            exit(e.message)

    print 'Building Docker file for service %(service_name)s, repo %(repo_name)s:' % locals()
    command = 'tar -czh . | docker build -t %(repo_name)s:latest -' % locals()
    print command
    call(command, shell=True)

    print 'Pushing %(repo_name)s:latest to docker-hub registry' % locals()
    command = 'docker push %(repo_name)s:latest' % locals()
    print command
    call(command, shell=True)

    # TODO: Running and testing docker container locally

    os.chdir('../ansible-deploy')
    print 'Deployed docker container to staging'
    command = 'ansible-playbook -i hosts --extra-vars "host=staging" --extra-vars ' \
              '"service=%s" ansible-deploy.yml' % service_name_to_repo[service_name]
    print command
    call(command, shell=True)

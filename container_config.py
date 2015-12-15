__author__ = 'erikfarmer'


import argparse
import os
from subprocess import call, check_output
from sys import exit, platform as _platform

VM_NOT_RUNNING_ERROR_MESSAGE = 'Virtual Machine is not running. Please start it with docker-machine start VM_NAME'
SERVICE_TO_DOCKERHUB_REPO = {'activity_service': 'activities-service',
                             'auth_service': 'authservice',
                             'user_service': 'user-service',
                             'resume_service': 'resume-parsing-service',
                             'candidate_service': 'candidate-service',
                             'base_service_container': 'base-service-container',
                             'social_network_service': 'social-network-service',
                             'candidate_pool_service': 'candidate-pool-service',
                             'spreadsheet_import_service': 'spreadsheet-import-service',
                             'scheduler_service': 'scheduler_service'}

SERVICE_TO_PORT_NUMBER = {'auth_service': 8001,
                          'activity_service': 8002,
                          'resume_service': 8003,
                          'user_service': 8004,
                         'candidate_service': 8005,
                    'social_network_service': 8006,
                    'candidate_pool_service': 8008,
                'spreadsheet_import_service': 8009,
                         'scheduler_service': 8010
}

parser = argparse.ArgumentParser(description='Common files administrator for Docker building.')
parser.add_argument('--build', nargs=1, choices=SERVICE_TO_DOCKERHUB_REPO.keys(), help='Invokes the Docker build action for given service')
parser.add_argument('--deploy', nargs=1, choices=SERVICE_TO_DOCKERHUB_REPO.keys(), help='Pushes to Dockerhub & deploys the latest container into staging environment')
parser.add_argument('--run', nargs=1, choices=SERVICE_TO_DOCKERHUB_REPO.keys(), help='Runs the container locally for given service')
args = parser.parse_args()


def set_environment_variables_from_env_output(env_output=''):
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


def attach_bash_shell_to_vm_if_not_linux():
    """
    If on OS X, use docker-machine to run Docker client.
    Must be in the service's dir to work
    """
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
            print ' > ', command
            set_environment_variables_from_env_output(check_output(command, shell=True))
        except Exception as e:
            exit(e.message)

if args.build:
    service_name = args.build[0]
    repo_name = "gettalent/%s" % SERVICE_TO_DOCKERHUB_REPO[service_name]
    print 'Changing dir to %s' % service_name
    os.chdir(service_name)

    attach_bash_shell_to_vm_if_not_linux()

    # Build Dockerfile
    print 'Building Docker file for service %(service_name)s, repo %(repo_name)s:' % locals()
    command = 'tar -czh . | docker build -t %(repo_name)s:latest -' % locals()
    print ' > ', command
    call(command, shell=True)

    # TODO: Running and testing docker container locally


if args.run:
    # Set up Docker env
    service_name = args.run[0]
    repo_name = "gettalent/%s" % SERVICE_TO_DOCKERHUB_REPO[service_name]
    print 'Changing dir to %s' % service_name
    os.chdir(service_name)

    attach_bash_shell_to_vm_if_not_linux()

    # from urllib2 import urlopen
    # my_ip = urlopen('http://ip.42.pl/raw').read()
    import socket
    my_ip = socket.gethostbyname(socket.gethostname())

    command = 'docker run -p %s:80 -p -e "GT_ENVIRONMENT=dev" --add-host=mysql_host:%s %s' % (
        SERVICE_TO_PORT_NUMBER[service_name],
        my_ip,
        repo_name)

    # print 'Running Docker container: %s' % service_name
    # os.chdir('../ansible-deploy')
    # command = 'ansible-playbook --connection=local --extra-vars "service=%s" ansible-run-local.yml' % \
    #           SERVICE_TO_DOCKERHUB_REPO[service_name]
    print ' > ', command
    call(command, shell=True)


if args.deploy:
    # Set up Docker env
    service_name = args.deploy[0]
    repo_name = "gettalent/%s" % SERVICE_TO_DOCKERHUB_REPO[service_name]
    print 'Changing dir to %s' % service_name
    os.chdir(service_name)

    attach_bash_shell_to_vm_if_not_linux()

    print 'Pushing %(repo_name)s:latest to docker-hub registry' % locals()
    command = 'docker push %(repo_name)s:latest' % locals()
    print ' > ', command
    call(command, shell=True)

    # Deploy to webdev via Ansible, unless building base service container
    if service_name == 'base_service_container':
        print 'This is the base-service-container, so not deploying anywhere'
    else:
        print 'Deploying docker container to staging'
        os.chdir('../ansible-deploy')
        command = 'ansible-playbook -i hosts --extra-vars "host=staging-%s" --extra-vars ' \
                  '"service=%s" ansible-deploy.yml' % (SERVICE_TO_DOCKERHUB_REPO[service_name], SERVICE_TO_DOCKERHUB_REPO[service_name])
        print ' > ', command
        call(command, shell=True)

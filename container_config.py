import subprocess

__author__ = 'erikfarmer'


import argparse
import os
from subprocess import call, check_output
from sys import exit, platform as _platform

VM_NOT_RUNNING_ERROR_MESSAGE = 'Virtual Machine is not running. Please start it with docker-machine start VM_NAME'
SERVICE_TO_REPO_NAME = {'base_service_container': 'base-service-container',
                        'auth_service': 'auth-service',
                        'activity_service': 'activity-service',
                        'resume_parsing_service': 'resume-parsing-service',
                        'user_service': 'user-service',
                        'candidate_service': 'candidate-service',
                        'social_network_service': 'social-network-service',
                        'widget_service': 'widget-service',
                        'candidate_pool_service': 'candidate-pool-service',
                        'spreadsheet_import_service': 'spreadsheet-import-service',
                        'scheduler_service': 'scheduler_service',
                        'sms_campaign_service': 'sms-campaign-service'
                        }

SERVICE_TO_PORT_NUMBER = {'auth_service': 8001,
                          'activity_service': 8002,
                          'resume_parsing_service': 8003,
                          'user_service': 8004,
                          'candidate_service': 8005,
                          'social_network_service': 8006,
                          'widget_service': 8007,
                          'candidate_pool_service': 8008,
                          'spreadsheet_import_service': 8009,
                          'scheduler_service': 8011,
                          'sms_campaign_service': 8012}

parser = argparse.ArgumentParser(description='Common files administrator for Docker building.')
parser.add_argument('--build', nargs=1, choices=SERVICE_TO_REPO_NAME.keys(), help='Invokes the Docker build action for given service')
parser.add_argument('--build-all', action='store_true', help='Invokes the Docker build action for all services except base_service_container')
parser.add_argument('--push-dockerhub', nargs=1, choices=SERVICE_TO_REPO_NAME.keys(), help='Pushes image to Dockerhub')
parser.add_argument('--push-dockerhub-all', action='store_true', help='Pushes all images to Dockerhub except base_service_container')
parser.add_argument('--push-ecr', nargs=1, choices=SERVICE_TO_REPO_NAME.keys(), help='Pushes image to Amazon EC2 Container Registry (ECR)')
parser.add_argument('--push-ecr-all', action='store_true', help='Pushes all images to Amazon EC2 Container Registry (ECR) except base_service_container')
parser.add_argument('--run', nargs=1, choices=SERVICE_TO_REPO_NAME.keys(), help='Runs the container locally for given service')
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


def build_docker_image(service_name):
    repo_name = "gettalent/%s" % SERVICE_TO_REPO_NAME[service_name]
    original_cwd = os.getcwd()

    print 'Changing dir to %s' % service_name
    os.chdir(service_name)

    attach_bash_shell_to_vm_if_not_linux()

    # Build Dockerfile
    print 'Building Docker file for service %(service_name)s, repo %(repo_name)s:' % locals()
    command = 'tar -czh . | docker build -t %(repo_name)s:latest -' % locals()
    print ' > ', command
    call(command, shell=True)

    print 'Moving back to original director: %s' % original_cwd
    os.chdir(original_cwd)


def push_image_to_ecr(service_name):
    repo_name = "gettalent/%s" % SERVICE_TO_REPO_NAME[service_name]
    ecr_registry_url = "528222547498.dkr.ecr.us-east-1.amazonaws.com"
    original_cwd = os.getcwd()

    attach_bash_shell_to_vm_if_not_linux()

    print 'Changing directory to pyenv 2.7.9 directory to access AWS CLI'
    python_bin_path = os.path.expanduser("~/.pyenv/versions/2.7.9/bin")
    command = 'cd %(python_bin_path)s' % locals()
    print ' > ', command
    os.chdir(python_bin_path)

    print 'Get ECR login command'
    command = 'aws ecr get-login --region us-east-1'
    print ' > ', command
    ecr_get_login_output = subprocess.check_output(args=["aws", "ecr", "get-login", "--region", "us-east-1"])

    print 'Docker login to ECR'
    print ' > ', ecr_get_login_output
    call(ecr_get_login_output, shell=True)

    print 'Tagging %(repo_name)s image with fully-qualified ECR path' % locals()
    command = 'docker tag -f %(repo_name)s:latest %(ecr_registry_url)s/%(repo_name)s:latest' % locals()
    print ' > ', command
    call(command, shell=True)

    print 'Pushing %(repo_name)s:latest to ECR registry at %(ecr_registry_url)s' % locals()
    command = 'docker push %(ecr_registry_url)s/%(repo_name)s:latest' % locals()
    print ' > ', command
    call(command, shell=True)

    print 'Moving back to original director: %s' % original_cwd
    os.chdir(original_cwd)


def push_image_to_dockerhub(service_name):
    repo_name = "gettalent/%s" % SERVICE_TO_REPO_NAME[service_name]
    original_cwd = os.getcwd()
    print 'Changing dir to %s' % service_name
    os.chdir(service_name)

    # Set up Docker env
    attach_bash_shell_to_vm_if_not_linux()

    print 'Pushing %(repo_name)s:latest to docker-hub registry' % locals()
    command = 'docker push %(repo_name)s:latest' % locals()
    print ' > ', command
    call(command, shell=True)

    print 'Moving back to original director: %s' % original_cwd
    os.chdir(original_cwd)


if args.build:
    service_name = args.build[0]
    build_docker_image(service_name)


if args.build_all:
    for service_name in SERVICE_TO_REPO_NAME.keys():
        if service_name == "base_service_container":
            print "Skipping base service container"
            continue
        print "Building Docker image for %s" % service_name
        build_docker_image(service_name)


if args.run:
    if 1 == 1:  # To get past PyCharm's "Code unreachable" warning.  (Only temporary)
        raise Exception("This doesn't work yet! Need to get MySQL set up")
    # Set up Docker env
    service_name = args.run[0]
    repo_name = "gettalent/%s" % SERVICE_TO_REPO_NAME[service_name]
    print 'Changing dir to %s' % service_name
    os.chdir(service_name)

    attach_bash_shell_to_vm_if_not_linux()

    # from urllib2 import urlopen
    # my_ip = urlopen('http://ip.42.pl/raw').read()
    import socket
    my_ip = socket.gethostbyname(socket.gethostname())

    command = 'docker run -p %s:80 -d -e "GT_ENVIRONMENT=dev" --add-host=mysql_host:%s %s' % (
        SERVICE_TO_PORT_NUMBER[service_name],
        my_ip,
        repo_name)
    print ' > ', command
    call(command, shell=True)


if args.push_dockerhub:
    service_name = args.push_dockerhub[0]
    push_image_to_dockerhub(service_name)


if args.push_ecr:
    service_name = args.push_ecr[0]
    push_image_to_ecr(service_name)


if args.push_ecr_all:
    for service_name in SERVICE_TO_REPO_NAME.keys():
        if service_name == "base_service_container":
            print "Skipping base service container"
            continue
        print "Pushing Docker image for %s to ECR" % service_name
        push_image_to_ecr(service_name)


if args.push_dockerhub_all:
    for service_name in SERVICE_TO_REPO_NAME.keys():
        if service_name == "base_service_container":
            print "Skipping base service container"
            continue
        print "Pushing Docker image for %s to ECR" % service_name
        push_image_to_dockerhub(service_name)

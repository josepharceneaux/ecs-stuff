"""
Script will create an AWS Lambda function deployment.

It expects there to be a deployments directory and it will create a
deployment of the form:
deployment_n
where n is incremented for each deployment based on the existing deployment directories.

This has been modified and linted from https://github.com/youngsoul/AlexaDeploymentSample
"""
import argparse
from shutil import copyfile

from resume_parsing_service.common.utils.lambda_utils import (
    _copy_deployment_files,
    _copy_virtual_env_libs,
    make_deployment_dir,
    zipdir
)

ROOT_DEPLOYMENTS_DIR = "./deployments"
DEPLOYMENT_FILES = [
    'libmysqlclient.so.18',
    'email_process.py',
    'models.py',
    'python.conf'
]


parser = argparse.ArgumentParser(description='Create an AWS Lambda Deployment for resume emails')
parser.add_argument('--env', required=True, choices=['prod', 'staging'],
                    help='Which environment would you like to create a build for?')
parser.add_argument('--venv', required=True,
                    help='What is the relative location of the virtual environment folder?')
args = parser.parse_args()

if args.env == 'prod':
    print 'Building a prod deployment'
    DEPLOYMENT_FILES.append('settings/prod/settings.py')
elif args.env == 'staging':
    print 'Building a staging deployment'
    DEPLOYMENT_FILES.append('settings/staging/settings.py')

def replace_mysql_deps(NEW_DEPLOYMENT_DIR):
    copyfile('_mysql.so', NEW_DEPLOYMENT_DIR + '/_mysql.so')


if __name__ == "__main__":
    (NEW_DEPLOYMENT_DIR, CURRENT_DEPLOYMENT_NAME) = make_deployment_dir(ROOT_DEPLOYMENTS_DIR)
    _copy_deployment_files(NEW_DEPLOYMENT_DIR, DEPLOYMENT_FILES)
    _copy_virtual_env_libs(NEW_DEPLOYMENT_DIR, args.venv, lib64=False) #previously True
    replace_mysql_deps(NEW_DEPLOYMENT_DIR)
    zipdir(NEW_DEPLOYMENT_DIR, "{0}/{1}.zip".format(ROOT_DEPLOYMENTS_DIR, CURRENT_DEPLOYMENT_NAME))

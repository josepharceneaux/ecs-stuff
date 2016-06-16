"""
Script will create an AWS Lambda function deployment.

It expects there to be a deployments directory and it will create a
deployment of the form:
deployment_n
where n is incremented for each deployment based on the existing deployment directories.

This has been modified and linted from https://github.com/youngsoul/AlexaDeploymentSample
"""
__author__ = 'erik@gettalent.com'
import argparse

from resume_parsing_service.common.utils.lambda_utils import (
    _copy_deployment_files,
    _copy_virtual_env_libs,
    make_deployment_dir,
    zipdir
)


ROOT_DEPLOYMENTS_DIR = "./deployments"
DEPLOYMENT_FILES = [
    'boto_utils.py',
    'burning_glass_utils.py',
    'lambda_handlers.py',
    'OauthLib.py',
    'optic_parsing_utils.py'
]


parser = argparse.ArgumentParser(description='Create an AWS Lambda Deployment for resume parsing')
parser.add_argument('--venv', required=True,
                    help='What is the relative location of the virtual environment folder?')
args = parser.parse_args()


if __name__ == "__main__":
    (NEW_DEPLOYMENT_DIR, CURRENT_DEPLOYMENT_NAME) = make_deployment_dir(ROOT_DEPLOYMENTS_DIR)
    _copy_deployment_files(NEW_DEPLOYMENT_DIR, DEPLOYMENT_FILES)
    _copy_virtual_env_libs(NEW_DEPLOYMENT_DIR, args.venv)
    zipdir(NEW_DEPLOYMENT_DIR, "{0}/{1}.zip".format(ROOT_DEPLOYMENTS_DIR, CURRENT_DEPLOYMENT_NAME))

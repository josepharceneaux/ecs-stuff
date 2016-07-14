#!/usr/bin/python
"""
Use this for:
-Installing any necessary frontend packages & updating them
-Env-specific building frontend assets
-Env-specific deployments to S3 Static Websites.

Usage examples:
./manage.py --update
./manage.py --build dev
./manage.py --deploy staging

"""

import argparse
import os
import sys
from subprocess import check_call

parser = argparse.ArgumentParser(description='For frontend-related actions.')
parser.add_argument('--build', nargs=1, choices=['local', 'dev', 'staging', 'prod'],
                    help='Builds assets to build/ directory for given environment')
parser.add_argument('--deploy', nargs=1, choices=['dev', 'staging', 'prod', 'demo'],
                    help='Deploys assets in build/ to S3 Static Website bucket for given environment, if you'
                         'have permissions')
parser.add_argument('--release', action='store_true',
                    help='Promote staging front end to production.')
parser.add_argument('--update', action='store_true',
                    help='Installs any necessary Bower packages & updates Bower')
parser.add_argument('--mock_ci', action='store_true',
                    help='Every minute, pulls, builds, and deploys, until process is killed')
args = parser.parse_args()

if args.deploy:
    env = args.deploy[0]

    build_dir_path = os.getcwd() + '/build'
    s3_bucket_name = 'app' if env == 'prod' else env  # S3 bucket subdomain is same as env, except prod -> app

    print 'Changing directory to pyenv 2.7.9 directory to access AWS CLI'
    python_bin_path = os.path.expanduser("~/.pyenv/versions/2.7.9/bin")
    command = 'cd %(python_bin_path)s' % locals()
    print ' > ', command
    os.chdir(python_bin_path)

    print 'Uploading to %s bucket' % env
    if env == 'demo':
        region = 'us-west-1'
    else:
        region = 'us-east-1'
    command = 'aws s3 sync %(build_dir_path)s s3://%(s3_bucket_name)s-gettalent-com --region %(region)s --acl public-read --cache-control no-cache' % locals()
    print ' > ', command
    check_call(command, shell=True, stdout=sys.stdout)


S3_STAGING = 's3://staging-gettalent-com'
S3_PROD = 's3://app-gettalent-com'
S3_REGION = 'us-east-1'
if args.release:
    print 'Changing directory to pyenv 2.7.9 directory to access AWS CLI'
    python_bin_path = os.path.expanduser("~/.pyenv/versions/2.7.9/bin")
    command = 'cd %(python_bin_path)s' % locals()
    print ' > ', command
    os.chdir(python_bin_path)

    command = "aws s3 sync {} {} --region {} --acl public-read --cache-control no-cache".format(S3_STAGING, S3_PROD, S3_REGION)
    print '>', command
    check_call(command, shell=True, stdout=sys.stdout)


if args.build:
    env = args.build[0]

    gt_node_env = {
        'local': 'local',
        'dev': 'development',
        'staging': 'development',
        'prod': 'production'
    }[env]

    print 'Building for %(env)s env' % locals()
    command = 'GT_ENVIRONMENT=%(gt_node_env)s npm run build' % locals()
    print ' > ', command
    check_call(command, shell=True, stdout=sys.stdout)


if args.update:
    print 'Installing Bower packages'
    command = 'bower install'
    print ' > ', command
    check_call(command, shell=True)

    print 'Updating Bower'
    command = 'npm install -g bower'
    print ' > ', command
    check_call(command, shell=True, stdout=sys.stdout)


if args.mock_ci:
    while True:
        print 'Pulling latest'
        command = 'git pull'
        print ' > ', command
        check_call(command, shell=True, stdout=sys.stdout)

        print 'Building everything'
        command = './manage.py --build prod'
        print ' > ', command
        check_call(command, shell=True, stdout=sys.stdout)

        print 'Deploying to dev'
        command = './manage.py --deploy dev'
        print ' > ', command
        check_call(command, shell=True, stdout=sys.stdout)

        print 'Sleeping 1m'
        import time
        time.sleep(60)

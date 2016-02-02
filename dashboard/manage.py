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
from subprocess import call

parser = argparse.ArgumentParser(description='For frontend-related actions.')
parser.add_argument('--build', nargs=1, choices=['local', 'dev', 'staging', 'prod'],
                    help='Builds assets to build/ directory for given environment')
parser.add_argument('--deploy', nargs=1, choices=['dev', 'staging', 'prod', 'demo'],
                    help='Deploys assets in build/ to S3 Static Website bucket for given environment, if you'
                         'have permissions')
parser.add_argument('--update', action='store_true',
                    help='Installs any necessary Bower packages & updates Bower')
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
    command = 'aws s3 sync %(build_dir_path)s s3://%(s3_bucket_name)s.gettalent.com --region %(region)s --acl public-read --cache-control no-cache' % locals()
    print ' > ', command
    call(command, shell=True)


if args.build:
    env = args.build[0]

    gt_node_env = {
        'local': 'local',
        'dev': 'development',
        'staging': 'development',
        'prod': 'production'
    }[env]

    print 'Building for %(env)s env' % locals()
    command = 'GT_NODE_ENV=%(gt_node_env)s gulp build' % locals()
    print ' > ', command
    call(command, shell=True)


if args.update:
    print 'Installing Bower packages'
    command = 'bower install'
    print ' > ', command
    call(command, shell=True)

    print 'Updating Bower'
    command = 'npm install -g bower'
    print ' > ', command
    call(command, shell=True)

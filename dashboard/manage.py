#!/usr/bin/python
"""
Use this for:
-Env-specific building frontend assets
-Env-specific deployments to S3 Static Websites.

Usage examples:
./manage.py --build dev
./manage.py --deploy staging

"""

import argparse
import os
from subprocess import call

parser = argparse.ArgumentParser(description='For frontend-related actions.')
parser.add_argument('--build', nargs=1, choices=['local', 'dev', 'staging', 'prod'],
                    help='Builds assets to build/ directory for given environment')
parser.add_argument('--deploy', nargs=1, choices=['dev', 'staging', 'prod'],
                    help='Deploys assets in build/ to S3 Static Website bucket for given environment, if you'
                         'have permissions')
args = parser.parse_args()

if args.deploy:
    env = args.deploy[0]

    build_dir_path = os.getcwd() + '/build'

    print 'Changing directory to pyenv 2.7.9 directory to access AWS CLI'
    python_bin_path = os.path.expanduser("~/.pyenv/versions/2.7.9/bin")
    command = 'cd %(python_bin_path)s' % locals()
    print ' > ', command
    os.chdir(python_bin_path)

    print 'Uploading to %s bucket' % env
    command = 'aws s3 sync %(build_dir_path)s s3://%(env)s.gettalent.com --region us-east-1 --acl public-read' % locals()
    print ' > ', command
    call(command, shell=True)


if args.build:
    env = args.build[0]

    gt_node_env = {
        'local': 'local',
        'staging': 'development',
        'prod': 'production'
    }[env]

    print 'Building for %(env)s env' % locals()
    command = 'GT_NODE_ENV=%(gt_node_env)s gulp build' % locals()
    print ' > ', command
    call(command, shell=True)



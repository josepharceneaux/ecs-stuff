#!/usr/bin/python
"""
Use this for:
-Env-specific Widget deployments to S3 Static Website Bucket.

Usage example:
./s3_uploader.py --deploy <env>

"""
__author__ = 'erik@gettalent'
import argparse
import os
from subprocess import call

parser = argparse.ArgumentParser(description='Deploys angular based widgets to appropriate s3 bucket for serving via CloudFront.')
parser.add_argument('--deploy', nargs=1, choices=['dev', 'staging', 'prod'],
                    help='Deploys angular app to S3 Static Website bucket for given environment, if you'
                         'have permissions')
args = parser.parse_args()

if args.deploy:
    env = args.deploy[0]
    widgets_dir = os.getcwd() + '/angularWidgets'
    s3_bucket_name = 'widgets'

    print 'Changing directory to pyenv 2.7.9 directory to access AWS CLI'
    python_bin_path = os.path.expanduser("~/.pyenv/versions/2.7.9/bin")
    command = 'cd {}'.format(python_bin_path)
    print ' > ', command
    os.chdir(python_bin_path)

    print 'Uploading to %s bucket' % env
    if env == 'dev':
        region = 'us-west-1'
    else:
        print 'Currently not supporting environments other than dev'
        exit()
    command = 'aws s3 sync {widgets_dir} s3://{s3_bucket_name}.gettalent.com --region {region} --acl public-read --cache-control no-cache'.format(
        widgets_dir=widgets_dir, s3_bucket_name=s3_bucket_name, region=region
    )
    print ' > ', command
    call(command, shell=True)
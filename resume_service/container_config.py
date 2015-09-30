__author__ = 'erikfarmer'


import argparse
import os
import shutil
from subprocess import call


parser = argparse.ArgumentParser(description='Common files administrator for Docker building.')
parser.add_argument('--copy', help='Copies the common files', action="store_true")
parser.add_argument('--build', help='Invokes the Docker build action', action="store_true")
args = parser.parse_args()
if args.copy:
    print 'Copying top level requirements'
    shutil.copy('../requirements.txt', './requirements.txt')
if args.build:
    print 'Building Docker file'
    call('docker build .', shell=True)
    os.remove('requirements.txt')

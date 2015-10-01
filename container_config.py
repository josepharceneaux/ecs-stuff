__author__ = 'erikfarmer'


import argparse
import os
import shutil
from subprocess import call


services = ['activities_service', 'auth_service', 'candidate_service', 'resume_service']
service_name_to_dockerhub_repo = {'activities_service': 'activities-service',
                        'auth_service': 'authservice',
                        'resume_service': 'resume-parsing-service',
                        'candidate_service': 'candidate-service'}

parser = argparse.ArgumentParser(description='Common files administrator for Docker building.')
parser.add_argument('--copy', help='Copies the common files', action="store_true")
parser.add_argument('--build', nargs=1, choices=services, help='Invokes the Docker build action for given service')
parser.add_argument('--clean', help='Invokes the clean action (removes common files from each service directory)', action="store_true")
args = parser.parse_args()

if args.copy:
    print 'Symlinking common requirements and models into services directories: %s' % services
    for service in services:
        # Symlink requirements
        requirements_symlink = '../requirements.txt'
        service_symlink = "./%s/requirements.txt" % service
        if os.path.islink(service_symlink):
            print "Symlink %s already exists" % service_symlink
        else:
            print "Creating symlink %s in %s" % (requirements_symlink, service_symlink)
            os.symlink(requirements_symlink, service_symlink)

        # Symlink models
        models_symlink = "../common/models"
        service_symlink = "./%s/models" % service
        if os.path.islink(service_symlink):
            print "Symlink %s already exists" % service_symlink
        else:
            print "Creating symlink %s in %s" % (models_symlink, service_symlink)
            os.symlink(models_symlink, service_symlink)

        # Symlink utils
        utils_symlink = "../common/utils"
        service_symlink = "./%s/utils" % service
        if os.path.islink(service_symlink):
            print "Symlink %s already exists" % service_symlink
        else:
            print "Creating symlink %s in %s" % (utils_symlink, service_symlink)
            os.symlink(utils_symlink, service_symlink)

if args.build:
    service_name = args.build[0]
    repo_name = "gettalent/%s" % service_name_to_dockerhub_repo[service_name]
    os.chdir(service_name)
    print 'Resolving symlinks and building Docker file for service %(service_name)s, repo %(repo_name)s:' % locals()
    command = 'tar -czh . | docker build -t %(repo_name)s:latest -' % locals()
    print command
    call(command, shell=True)


if args.clean:
    print 'Deleting common requirements and models from services directories: %s' % services
    for service in services:
        # Symlink requirements
        service_symlink = "./%s/requirements.txt" % service
        try:
            print "Removing %s" % service_symlink
            os.remove(service_symlink)
        except Exception:
            print "Couldn't remove %s" % service_symlink

        # Symlink models
        service_symlink = "./%s/models" % service
        try:
            print "Removing %s" % service_symlink
            os.remove(service_symlink)
        except Exception:
            print "Couldn't remove %s" % service_symlink

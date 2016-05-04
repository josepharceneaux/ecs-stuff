"""
Script will create an AWS Lambda function deployment.

It expects there to be a deployments directory and it will create a
deployment of the form:
deployment_n
where n is incremented for each deployment based on the existing deployment directories.

This has been modified and linted from https://github.com/youngsoul/AlexaDeploymentSample
"""
import argparse
import os
import subprocess
import zipfile

parser = argparse.ArgumentParser(description='Create an AWS Lambda Deployment for resume emails')
parser.add_argument('--env', required=True, choices=['prod', 'staging'],
                    help='Which environment would you like to create a build for?')
parser.add_argument('--venv', required=True,
                    help='What is the relative location of the virtual environment folder?')
args = parser.parse_args()

ROOT_DEPLOYMENTS_DIR = "./deployments"

"""
List of files that should be included in the deployment
Only the files listed here, and the libraries in the requirements.txt
file will be included in the deployment.
"""
DEPLOYMENT_FILES = ['email_process.py', 'python.conf', 'models.py', '/usr/lib64/libmysqlclient.so.18']

if args.env == 'prod':
    print 'Building a prod deployment'
    DEPLOYMENT_FILES.append('settings/prod/settings.py')
elif args.env == 'staging':
    print 'Building a staging deployment'
    DEPLOYMENT_FILES.append('settings/staging/settings.py')


def get_library_requirements():
    """Returns a list where each item is a library to install"""
    with open("./requirements.txt", 'r') as infile:
        install_requirements = infile.readlines()

    return install_requirements


def get_immediate_subdirectories(a_dir):
    """
    :param str a_dir: The directory we want to get the subdirectories of.
    :return list:
    """
    return [name for name in os.listdir(a_dir)
            if os.path.isdir(os.path.join(a_dir, name))]


def make_deployment_dir():
    """Creates a deployment directory.
    *** CAUTION ***
    Deployments should be handled by a DevOps or the DRI for this service to avoid trying to make
    the directories at the same time (rare).
    The lines:
    if not os.path.exists(directory):
        os.makedirs(directory)
    Does create a small race condition window
    (http://stackoverflow.com/questions/273192/how-to-check-if-a-directory-exists-and-create-it-if-necessary).
    :return tuple (str, str):
    """
    all_deployment_directories = get_immediate_subdirectories(ROOT_DEPLOYMENTS_DIR)
    max_deployment_number = -1
    for deployment_dir in all_deployment_directories:
        dir_name_elements = deployment_dir.split("_")
        if int(dir_name_elements[1]) > max_deployment_number:
            max_deployment_number = int(dir_name_elements[1])

    if max_deployment_number == -1:
        max_deployment_number = 0

    deployment_name = "deployment_{0}".format(max_deployment_number+1)
    new_deployment_dir_path = "{0}/{1}".format(ROOT_DEPLOYMENTS_DIR, deployment_name)

    if not os.path.exists(new_deployment_dir_path):
        os.mkdir(new_deployment_dir_path)

    return new_deployment_dir_path, deployment_name

# Keeping this temporarily in the event _copy_virtual_env_libs causes unforeseen complications.
# def _install_requirements(deployment_reqs, deployment_dir):
#     """
#     pip install <requirements line> -t <deployment_dir>
#     :param deployment_reqs
#     :param deployment_dir:
#     :return:
#     """
#     if os.path.exists(deployment_dir):
#         for requirement in deployment_reqs:
#             cmd = "pip install {0} -t {1}".format(requirement, deployment_dir).split()
#             unused_return_code = subprocess.call(cmd, shell=False)


def _copy_virtual_env_libs(deployment_dir, venv_folder):
    """
    Copies the installed libraries from the virtual environment library dirs.
    :param deployment_dir: The name of the new deployment directory before zipping.
    :param venv_folder: The name of the virtual environment directory.
    :return:
    """
    print deployment_dir
    print venv_folder
    if os.path.exists(venv_folder):
        lib_dir = "{}/lib/".format(venv_folder)
        lib64_dir = "{}/lib64/".format(venv_folder)
        lib_cmd = "cp -r {0} {1}".format(lib_dir, deployment_dir)
        lib64_cmd = "cp -r {0} {1}".format(lib64_dir, deployment_dir)
        unused_lib_cmd_code = subprocess.call(lib_cmd, shell=True)
        unused_lib64_cmd_code = subprocess.call(lib64_cmd, shell=True)
    else:
        raise UserWarning('Virtual environment folder not found.')
    pass


def _copy_deployment_files(deployment_dir):
    """
    Puts deployment files in a specified deployment directory.
    :param str deployment_dir:
    """
    # Keeping this commented out, will likely reinclude this when/if we move resumeParsing to
    # AWS Lambda. `usr` contains binaries built on an Amazon AMI.
    # lib_cmd = "cp -r {0} {1}".format('usr', deployment_dir).split()
    # unused_lib_cmd_code = subprocess.call(lib_cmd, shell=False)
    for deployment_file in DEPLOYMENT_FILES:
        if os.path.exists(deployment_file):
            cmd = "cp {0} {1}".format(deployment_file, deployment_dir).split()
            unused_return_code = subprocess.call(cmd, shell=False)
        else:
            raise NameError("Deployment file not found [{0}]".format(deployment_file))


def zipdir(dir_path=None, zip_file_path=None, include_dir_in_zip=False):
    """
    Attribution:  I wish I could remember where I found this on the
    web.  To the unknown sharer of knowledge - thank you.

    Create a zip archive from a directory.
    Note that this function is designed to put files in the zip archive with
    either no parent directory or just one parent directory, so it will trim any
    leading directories in the filesystem paths and not include them inside the
    zip archive paths. This is generally the case when you want to just take a
    directory and make it into a zip file that can be extracted in different
    locations.

    :param str dir_path: path to the directory to archive. This is the only
    required argument. It can be absolute or relative, but only one or zero
    leading directories will be included in the zip archive.
    :param str zip_file_path: path to the output zip file. This can be an absolute
    or relative path. If the zip file already exists, it will be updated. If
    not, it will be created. If you want to replace it from scratch, delete it
    prior to calling this function. (default is computed as dirPath + ".zip")
    :param bool include_dir_in_zip: indicator whether the top level directory should
    be included in the archive or omitted. (default True)
"""
    if not zip_file_path:
        zip_file_path = dir_path + ".zip"
    if not os.path.isdir(dir_path):
        raise OSError("dirPath argument must point to a directory. "
                      "'%s' does not." % dir_path)
    parent_dir, dir_to_zip = os.path.split(dir_path)

    # Little nested function to prepare the proper archive path
    def trim_path(path):
        archive_path = path.replace(parent_dir, "", 1)
        if parent_dir:
            archive_path = archive_path.replace(os.path.sep, "", 1)
        if not include_dir_in_zip:
            archive_path = archive_path.replace(dir_to_zip + os.path.sep, "", 1)
        return os.path.normcase(archive_path)

    out_file = zipfile.ZipFile(zip_file_path, "w", compression=zipfile.ZIP_DEFLATED)
    for (archive_dir_path, dir_names, file_names) in os.walk(dir_path):
        for file_name in file_names:
            file_path = os.path.join(archive_dir_path, file_name)
            out_file.write(file_path, trim_path(file_path))
        # Make sure we get empty directories as well
        if not file_names and not dir_names:
            zip_info = zipfile.ZipInfo(trim_path(archive_dir_path) + "/")
            out_file.writestr(zip_info, "")
    out_file.close()


if __name__ == "__main__":
    (NEW_DEPLOYMENT_DIR, CURRENT_DEPLOYMENT_NAME) = make_deployment_dir()
    _copy_deployment_files(NEW_DEPLOYMENT_DIR)
    DEPLOYMENT_REQUIREMENTS = get_library_requirements()
    _copy_virtual_env_libs(NEW_DEPLOYMENT_DIR, args.venv)
    zipdir(NEW_DEPLOYMENT_DIR, "{0}/{1}.zip".format(ROOT_DEPLOYMENTS_DIR, CURRENT_DEPLOYMENT_NAME))

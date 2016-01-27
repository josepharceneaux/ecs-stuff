"""
Functions related to EC2 instances.

"""

import requests


def get_ec2_instance_id():
    """
    :rtype: str | None
    :return:
    """
    ec2_instance_id = None
    try:
        ec2_instance_id = requests.get('http://instance-data/latest/meta-data/instance-id').content
    except:
        pass
    return ec2_instance_id

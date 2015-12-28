# -*- coding: utf-8 -*-
"""Class to manage property keys and values specific to the application environment (e.g. prod, staging, local).

In a developer's local environment, the file given by the below LOCAL_CONFIG_PATH contains the property keys and values.

﻿In prod and staging environments, the above config file does not exist.
Rather, the properties are obtained from EC2 tags whose key follows the format ﻿﻿﻿"section_name|key_name".
For example, the environment's S3 bucket would be given by an EC2 tag whose key is s3_bucket.
"""

import os
import boto
import boto.utils
import boto.ec2
import logging
import error_handling
from ConfigParser import SafeConfigParser
from enum import Enum


LOCAL_CONFIG_PATH = "~/.talent/web.cfg"

EC2_TAG_SECTION_SEPARATOR = "|"  # separates section name from key name in EC2 tags

REGION_KEY = "region"
DOMAIN_KEY = "domain"
EMAIL_KEY = "email"
ENV_KEY = "env"
ACCOUNT_ID_KEY = "account-id"
BUCKET_KEY = "bucket"
INSTANCE_NAME = 'instance-name'


class PropertySection(Enum):
    cloudsearch = [DOMAIN_KEY, REGION_KEY]
    local = [EMAIL_KEY, ENV_KEY, INSTANCE_NAME]
    iam = [ACCOUNT_ID_KEY]
    s3 = [BUCKET_KEY, REGION_KEY]


_config = None


def _get_ec2_tag_dict():
    try:
        instance_metadata = boto.utils.get_instance_metadata(num_retries=3)
        instance_id = instance_metadata['instance-id']
    except:
        return dict()
    conn_us = boto.ec2.connect_to_region('us-west-1')
    instance_reservations = conn_us.get_all_instances(instance_ids=[instance_id])
    available_tags_dict = instance_reservations[0].instances[0].tags
    available_tags_set = available_tags_dict.viewkeys()

    # Get the property tags we're expecting: They're in "section|key" format.
    expected_tags_set = {"Name"}  # Name is the default EC2 tag
    for section_name, key_names_enum in PropertySection.__members__.items():
        for key_name in key_names_enum.value:
            expected_tags_set.add("%s%s%s" % (section_name, EC2_TAG_SECTION_SEPARATOR, key_name))

    if available_tags_set != expected_tags_set:
        logging.warn("Available tags did not match expected tags in instance %s.\nAvailable tags: %s\nExpected tags: %s",
                            instance_id,
                            available_tags_set,
                            expected_tags_set)

    return available_tags_dict


def get_env():
    """

    :return: 'prod', 'qa', or 'dev'
    """
    return _get_config_parser().get(PropertySection.local.name, ENV_KEY)


def get_email():
    return _get_config_parser().get(PropertySection.local.name, EMAIL_KEY)


def get_cloudsearch_domain_name():
    return _get_config_parser().get(PropertySection.cloudsearch.name, DOMAIN_KEY)


def get_cloudsearch_region():
    return _get_config_parser().get(PropertySection.cloudsearch.name, REGION_KEY)


def get_s3_bucket_name():
    return _get_config_parser().get(PropertySection.s3.name, BUCKET_KEY)


def get_s3_region():
    """

    :return: if returns '', uses S3 default region
    """
    return _get_config_parser().get(PropertySection.s3.name, REGION_KEY)


def get_aws_account_id():
    return _get_config_parser().get(PropertySection.iam.name, ACCOUNT_ID_KEY)


def get_instance_id():
    return _get_config_parser().get(PropertySection.local.name, INSTANCE_NAME)


def _get_config_parser():
    global _config

    if not _config:
        _config = SafeConfigParser()

        expanded_config_path = os.path.expanduser(LOCAL_CONFIG_PATH)
        if os.path.isfile(expanded_config_path):
            # Local developer setup: Has config file on local file system
            _config.read(expanded_config_path)
        else:
            # Webdev or prod setup: Has EC2 tag dict
            ec2_tag_dict = _get_ec2_tag_dict()
            if not ec2_tag_dict:
                logging.error("No config file or EC2 dictionary found")
                raise error_handling.InternalServerError("Error - no config file or EC2 dictionary found", 500)

            # Go through all sections & their properties & set config from them
            for section_name, key_names_enum in PropertySection.__members__.items():
                _config.add_section(section_name)
                for key_name in key_names_enum.value:
                    property_value = ec2_tag_dict.get("%s%s%s" % (section_name, EC2_TAG_SECTION_SEPARATOR, key_name))
                    _config.set(section_name, key_name, value=property_value)

    return _config

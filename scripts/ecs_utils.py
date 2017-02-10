import boto3

# ECS cluster name
STAGE_CLUSTER_NAME = 'stage'
PROD_CLUSTER_NAME = 'prod'

# ECS service suffix we use
STAGE_SVC_SUFFIX = '-stage'
PROD_SVC_SUFFIX = '-svc'

# ECS Task definition suffix we use
STAGE_TD_SUFFIX = '-stage-td'
PROD_TD_SUFFIX = '-td'

SERVICES_SUFFIX_DICT = { STAGE_CLUSTER_NAME : STAGE_SVC_SUFFIX, PROD_CLUSTER_NAME : PROD_SVC_SUFFIX }
TASKS_SUFFIX_DICT = { STAGE_CLUSTER_NAME : STAGE_TD_SUFFIX, PROD_CLUSTER_NAME : PROD_TD_SUFFIX }

# Base of our namespace for several structures
ECS_BASE_PATH = 'gettalent'

# How many previous Task Definitions (and related ECR images) to keep, not including the currently running one
GC_THRESHOLD = 3


def fatal(message):
    """
    Print error message and exit with 1
    """
    print message
    exit(1)


def validate_http_status(request_name, response):
    """
    Validate that we got a good status on our request.

    :param string request_name: Caller name to put in error message.
    :param json response: The response to be validated.
    :return: None.
    """
  
    try:
        http_status = response['ResponseMetadata']['HTTPStatusCode']
    except Exception as e:
        fatal("Exception getting HTTP status {}: {}".format(request_name, e.message))

    if http_status != 200:
        fatal("Error with {}. HTTP Status: {}".format(request_name, http_status))


#
# ECR (ECS Container Registry) functions
#


def tag_exists_in_repo(repo_path, tag):
    """
    Search for an image with a specific tag in a docker repository.

    :param string repo_name: The path of the repository to search.
    :param string tag: The tag to search for.
    :rtype: bool
    """

    ecr_client = boto3.client('ecr')

    response = ecr_client.list_images(repositoryName=repo_path)
    validate_http_status('list_images', response)
    while True:
        image_ids = response['imageIds']
        for image in image_ids:
            if 'imageTag' in image and image['imageTag'] == tag:
                return True

        if 'nextToken' not in response:
            break

        response = ecr_client.list_images(repositoryName=repo_path, nextToken=response['nextToken'])
        validate_http_status('list_images', response)

    return False


def image_exists_in_repo(name, image):
    """
    Search for an image with a specific tag in a docker repository.

    :param string name: The name of the repository to search.
    :param string image: The image and tag to search for.
    :rtype: bool
    """

    repo_path = ECS_BASE_PATH + "/" + name
    tag = image.split(':')[1]
    return tag_exists_in_repo(repo_path, tag)


def gather_images_from_repository(ecr_client, name, tags):
    """
    Collect images from repository.

    :param object ecr_client: ECR object from boto.
    :param string name: Repository name.
    :param string tags: Can be 'none', 'only', 'all' - return untagged, tagged, or all images.
    """

    if tags not in [ 'none', 'only', 'all' ]:
        raise Exception("gather_images_in_repo: parameter TAGS must be 'none', 'only', or 'all'. Called with {}".format(tags))

    service_uri = ECS_BASE_PATH + '/' + name

    response = ecr_client.list_images(repositoryName=service_uri)
    validate_http_status('list_images', response)

    return_list = []
    while True:
        image_list = response['imageIds']

        for image in image_list:
            if 'imageTag' in image:
                if tags == 'only' or tags == 'all':
                    return_list.append(image)
            else:
                if tags == 'none' or tags == 'all':
                    return_list.append(image)

        if 'nextToken' not in response:
            break

        response = ecr_client.list_images(repositoryName=service_uri, nextToken=response['nextToken'])
        validate_http_status('list_images', response)

    return return_list


def sort_image_list_by_tag(image_list):
    """
    Sort a list of ECR images by their tag.

    :param json image_list: A list of ECR imgaes.
    """

    return sorted(image_list, key=lambda x:x['imageTag'])


def repository_components_from_uri(uri):
    """
    Break up and return the constituent components of a container URI.

    :param string uri: URI of a container.
    """

    components = uri.split(':')
    if len(components) != 2:
        raise Exception("image_digest_from_uri called with invalid uri {}: no tag".format(uri))

    base = components[0]
    tag = components[1]
    components = base.split('/')
    if len(components) != 3:
        raise Exception("image_digest_from_uri called with invalid uri {}: bad base uri".format(uri))

    repo_name = components[1] + '/' + components[2]
    return repo_name, components[2], tag


def image_digest_from_tag(digest_list, tag):
    """
    Look for a container image with a certain tag.

    :param list[str] digest_list: A list of container digests and tags in JSON.
    :param string tag: The tag to search for.
    """

    entry = [ e for e in digest_list if e['imageTag'] == tag ]
    if entry:
        return entry[0]['imageDigest']

    return None


MAX_CONTAINER_DELETIONS = 100

def delete_images_from_repository_by_digest(ecr_client, repository_name, digest_list):
    """
    Delete a list of containers. ECR will only delete a certain number at a time, so we iterate.

    :param boto3.client ecr_client: The boto ECR (EC2 Container Registry) object.
    :param string repository_name: Name of the repository we're deleting from.
    :param list[str] digest_list: List of tagged containers found for the particular repository (in JSON).

    """

    while len(digest_list) > 0:
        n = min(len(digest_list), MAX_CONTAINER_DELETIONS)
        to_delete = digest_list[:n]

        response = ecr_client.batch_delete_image(repositoryName=repository_name, imageIds=to_delete)
        validate_http_status('batch_delete_image', response)

        if len(response['failures']) > 0:
            print "WARNING: failures deleting images in {}".format(repository_name)
            for fail in response['failures']:
                print "    {}".format(fail)

        del digest_list[:n]
        print "Deleted {}".format(n)


def delete_images_from_repository_by_uri(ecr_client, image_list, digest_list):
    """
    Given a list of container URIs. Find the digest SHA for the container and delete it. It's done this way because AWS uses
    a URI to specify a container on a task definition, but deleting the container requires the digest.

    :param object ecr_client: The boto ECR (EC2 Container Registry) object.
    :param list[str] image_list: List of ECR container URIs to be removed.
    :param list[str] digest_list: List of tagged containers found for the particular service (in JSON).
    """

    to_delete = []
    for image in image_list:
        repository_name, service_name, tag = repository_components_from_uri(image)
        digest = image_digest_from_tag(digest_list, tag)
        if digest:
            to_delete.append({ 'imageDigest' : digest, 'imageTag' : tag })
            print "Deleting {}".format(image)
        else:
            print "WARNING: Can't find digest for {}. Not deleted.".format(image)

    # Note that repository_name is repeatedly set in the loop above, but it will never change in this function.
    if len(to_delete) > 0:
        delete_images_from_repository_by_digest(ecr_client, repository_name, to_delete)


def remove_untagged_containers(ecr_client, service):
    """
    Remove any ECR containers which don't have a tag.
    
    :param string service: Name of the getTalent service.
    :param string cluster: name of the cluster to inspect.
    """

    repository_name = ECS_BASE_PATH + "/" + service

    # Collect all untagged containers for this service
    digest_list = gather_images_from_repository(ecr_client, service, 'none')
    delete_images_from_repository_by_digest(ecr_client, repository_name, digest_list)


#
# Task Definition functions
#


def gather_task_definitions(ecs_client, service, cluster):
    """
    Collect all task definitions for getTalent service in a cluster.

    :param boto3.client ecs_client: The boto ECS object.
    :param string service: Name of the getTalent service.
    :param string cluster: name of the cluster to inspect.
    """

    # Adjust to our ECS naming convention
    if cluster not in TASKS_SUFFIX_DICT:
        raise Exception("gather_task_definitions called with invalid cluster name {}".format(cluster))
    service = service + TASKS_SUFFIX_DICT[cluster]

    try:
        response = ecs_client.list_task_definitions(familyPrefix=service, status='ACTIVE', sort='DESC')
        validate_http_status('list_task_definitions', response)
    except Exception as e:
        print "Exception {} updating service for {}".format(e.message, service)
        return None

    td_list = []
    while True:
        arn_list = response['taskDefinitionArns']
        for arn in arn_list:
            td_list.append(arn)

        if 'nextToken' not in response:
            break

        response = ecs_client.list_task_definitions(familyPrefix=service, status='ACTIVE', sort='DESC', )
        validate_http_status('list_task_definitions', response, nextToken=response['nextToken'])

    return td_list


def gather_all_td_images(ecs_client, service):
    """
    Gather the images used by all ACTIVE task definitions.

    :param boto3.client ecs_client: ECS client object
    :param string service: The name of the service we're collecting from.
    :rtype: list[dict] All image URIs associated with task definitions for this service.
    """

    stage_td_list = gather_task_definitions(ecs_client, service, 'stage')
    prod_td_list = gather_task_definitions(ecs_client, service, 'prod')

    image_list = []
    for td_arn in stage_td_list:
        image_list.append(task_definition_image(ecs_client, td_arn))
    for td_arn in prod_td_list:
        image_list.append(task_definition_image(ecs_client, td_arn))

    return image_list


def task_definition_image(ecs_client, td_arn):
    """
    Return the image URI used by a task definition.

    :param boto3.client ecs_client: ECS client object
    :param string td_arn: The AWS Resource Name.
    """

    response = ecs_client.describe_task_definition(taskDefinition=td_arn)
    validate_http_status('describe_task_definition', response)
    if len(response['taskDefinition']['containerDefinitions']) > 1:
        return None

    return response['taskDefinition']['containerDefinitions'][0]['image']


def deregister_task(ecs_client, td_arn):
    """
    Make a task definition revision inactive.

    :param boto3.client ecs_client: ECS client object
    :param string td_arn: The AWS Resource Name.
    """

    print "Deactivating Task Definition {}".format(td_arn)
    response = ecs_client.deregister_task_definition(taskDefinition=td_arn)
    validate_http_status('derigester_task_definition', response)
    if response['taskDefinition']['status'] != 'INACTIVE':
        print "WARNING: {} not marked INACTIVE".format(td_arn)


#
# Service functions
#


# def gt_service_name_from_arn(service_arn):
#     """
#     Extract the getTalent service name from an AWS service ARN.
#
#     :param string service_arn: Amazon Resource Name
#     """
#     print "ARN: {}".format(service_arn)
#     revision = service_arn.split('/')[1].split(':')
#     print "REVISIN: {}".format(revision)
#     if len(revision) == 1:
#         return revision[0], None
#     else:
#         return revision[0], revision[1]


def get_all_services(ecs_client, cluster):
    """
    Gather all services running in an ECS cluster.

    :param boto3.client ecs_client: ECS client object
    :param string cluster: Name of the cluster.
    :rtype list | None
    """
    try:
        response = ecs_client.list_services(cluster=cluster)
        validate_http_status('list_services', response)
    except Exception as e:
        print "Exception {} get_all_services for cluster {}".format(e.message, cluster)
        return None

    service_list = []
    while True:
        arn_list = response['serviceArns']
        for service_arn in arn_list:
            service_name = service_arn.split('/')[-1]
            service_list.append(service_name)

        if 'nextToken' not in response:
            break

        response = ecs_client.list_services(cluster=cluster, nextToken=response['nextToken'])
        validate_http_status('list_services', response)

    return service_list


def update_service_task_definition(ecs_client, cluster, service, adjustment):
    """
    Move the task definition used by a service forwards or backwards.

    :param boto3.client ecs_client: ECS client object
    :param string cluster: Cluster name.
    :param string service: GT service name.
    :param string adjustment: How much to advance or regress the tack definition. E.g., +1, -2
    :rtype boolean:
    """
    if cluster not in SERVICES_SUFFIX_DICT:
        print "update_service_task_definition called with invalid cluster name {}".format(cluster)
        return False

    service_name = service + SERVICES_SUFFIX_DICT[cluster]

    # Get all active Task Definitions, in descending order
    td_arn_list = gather_task_definitions(ecs_client, service, cluster)

    # Determine the current Task Definition
    try:
        response = ecs_client.describe_services(cluster=cluster, services=[service_name])
        validate_http_status("describe_services: {}".format(service_name), response)
    except Exception as e:
        print "Exception {} updating service for {}".format(e.message, service_name)
        return False

    service_list = response['services']
    if len(service_list) > 1:
        # TODO: Test on multiple deployment and ensure TDs are the same
        print "WARNING: More than one service found for {}\nUsing first.".format(service_name)
    current_td_arn = service_list[0]['taskDefinition']
    desired_count = response['services'][0]['desiredCount']
    deployment_configuration = response['services'][0]['deploymentConfiguration']

    # Figure out where the current TD is in the list. index() can throw an exception if not found - exit gracefully.
    try:
        td_index = td_arn_list.index(current_td_arn)
    except Exception as e:
        print "ERROR: Current Task Definition not found in active Task Definition list for {}".format(service_name)
        return False

    # Since the TD list is in descending order, reverse the sign of the offset
    offset = int(adjustment) * -1
    if (td_index + offset) > (len(td_arn_list) - 1) or (td_index + offset) < 0:
        print "Adjustment {} out of range for {}".format(adjustment, service_name)
        return False

    try:
        replacement_td_arn = td_arn_list[td_index + offset]
    except Exception as e:
        print "Replacement Task Definition not available for {}: {}".format(service_name, e.message)
        return False

    # Update the service
    # TODO: This is also used in move-stage-to-prod.py - refactor into a function.
    print "Replacing:\n    {}\nwith\n    {}".format(current_td_arn, replacement_td_arn)
    try:
        response = ecs_client.update_service(cluster=cluster, service=service_name, desiredCount=desired_count,
                                             taskDefinition=replacement_td_arn, deploymentConfiguration=deployment_configuration)
        validate_http_status("update_service: {}".format(service_name), response)
    except Exception as e:
        print "Exception {} updating service for {}".format(e.message, service_name)
        return False

    return True


#
# Garbage Collection of all the things
#

def garbage_collect_ecs(service, cluster):
    """
    Garbage collect Task Definitions revisions and their associated ECR images.

    :param string service: Name of the getTalent service.
    :param string cluster: name of the cluster to inspect.
    :rtype None:
    """

    # Adjust to our ECS naming convention
    if cluster not in SERVICES_SUFFIX_DICT:
        raise Exception("garbage_collect_ecs called with invalid cluster name {}".format(cluster))
    service_name = service + SERVICES_SUFFIX_DICT[cluster]

    ecs_client = boto3.client('ecs')
    ecr_client = boto3.client('ecr')

    # Find the currently running task definition
    response = ecs_client.describe_services(cluster=cluster, services=[ service_name ])
    validate_http_status('describe_services', response)
    if len(response['services']) != 1:
        raise Exception("garbage_collect_ecs: More than one service returned for {}".format(service_name))
    current_td = response['services'][0]['taskDefinition']
    current_image = task_definition_image(ecs_client, current_td)

    # Get a list of all ACTIVE task definitions
    td_arn_list = gather_task_definitions(ecs_client, service, cluster)

    # Remove the task definition attached to the currently active service from our list
    if current_td in td_arn_list:
        td_arn_list.remove(current_td)
    else:
        print "WARNING: Currently running task definition {} for {} not found in Task Definition list.".format(current_td, service_name)

    # Cull the newest revisions that we want to keep out of the list
    if len(td_arn_list) > GC_THRESHOLD:
        count = 0
        while count < GC_THRESHOLD:
            del td_arn_list[0] 
            count += 1

    # Gather all the images from our updated task def list
    image_delete_list = []
    for arn in td_arn_list:
        image = task_definition_image(ecs_client, arn)
        if not image:
            print "WARNING: service {} Task Definition {} container numbers not 0.".format(service_name, arn)
            td_arn_list.remove(arn)
        else:
            image_delete_list.append(image)

    # Remove the task definitions on our list
    for arn in td_arn_list:
        deregister_task(ecs_client, arn)

    # Now that we've removed the TDs, gather the images from remaining definitions, stage and prod
    live_image_uri_list = gather_all_td_images(ecs_client, service)
    # And remove them from our deletion list, since they may be in use
    image_delete_list = [ i for i in image_delete_list if i not in live_image_uri_list ]

    print
    # Remove the images from our list, unless the current service uses it
    if current_image in image_delete_list:
        image_delete_list.remove(current_image)

    # Get a list of the tagged images for this repository so we can get the digest
    digest_list = gather_images_from_repository(ecr_client, service, 'only')
    delete_images_from_repository_by_uri(ecr_client, image_delete_list, digest_list)

    # Remove any untagged containers
    remove_untagged_containers(ecr_client, service)

    # TODO: go through all images and remove any dangling ones (those not attached to a task definition)
    # all_images = gather_images_from_repository(ecr_client, service, 'all')
    # image_delete_list = [ i for i in all_images if i not in live_image_uri_list ]
    # delete_images_from_repository_by_uri(ecr_client, image_delete_list, digest_list)

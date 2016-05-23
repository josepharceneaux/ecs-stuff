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

def validate_http_status(request_name, response):
    """
    Validate that we got a good status on our request.

    :param str request_name: Caller name to put in error message.
    :param json response: The response to be validated.
    :return: None.
    """
  
    try:
        http_status = response['ResponseMetadata']['HTTPStatusCode']
    except Exception as e:
        print "Exception getting HTTP status {}: {}".format(request_name, e.message)
        exit(1)

    if http_status != 200:
        print "Error with {}. HTTP Status: {}".format(request_name, http_status)
        exit(1)


# ECR (ECS Container Registry) functions


def tag_exists_in_repo(repo_path, tag):
    """
    Search for an image with a specific tag in a docker repository.

    :param str repo_name: The path of the repository to search.
    :param str tag: The tag to search for.
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

    :param str name: The name of the repository to search.
    :param str image: The image and tag to search for.
    :rtype: bool
    """

    repo_path = ECS_BASE_PATH + "/" + name
    tag = image.split(':')[1]
    return tag_exists_in_repo(repo_path, tag)


def gather_images_from_repo(name, tags):
    """
    Collect images from repository.

    :param str name: Repository name.
    :param str tags: Can be 'none', 'only', 'all' - return untagged, tagged, or all images.
    """

    if tags not in [ 'none', 'only', 'all' ]:
        raise Exception("gather_images_in_repo: parameter TAGS must be 'none', 'only', or 'all'. Called with {}".format(tags))

    ecr_client = boto3.client('ecr')
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


def delete_images_from_repository(ecr_client, image, service_name):
    """
    """

    components = image.split(':')
    image_ids = [ { 'imageDigest' : components[0], 'imageTag': components[1] } ]
    repository_uri = ECS_BASE_PATH + '/' + service_name

    response = ecr_client.batch_delete_image(repositoryName=repository_uri, imageIds=image_ids)
    validate_http_status('batch_delete_image', response)

    failures = len(response['failures'])
    if failures > 0:
        print "{} failures"

    print response


# Task Definition functions


def gather_task_definitions(ecs_client, service, cluster):
    """
    Collect all task definitions for getTalent service in a cluster.

    :param str service: Name of the getTalent service.
    :param str cluster: name of the cluster to inspect.
    """

    # Adjust to our ECS naming convention
    if cluster not in TASKS_SUFFIX_DICT:
        raise Exception("gather_task_definitions called with invalid cluster name {}".format(cluster))
    service = service + TASKS_SUFFIX_DICT[cluster]

    response = ecs_client.list_task_definitions(familyPrefix=service, status='ACTIVE', sort='DESC')
    validate_http_status('list_task_definitions', response)

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


def task_definition_image(ecs_client, td_arn):
    """
    Return the image used by a task definition.
    """

    response = ecs_client.describe_task_definition(taskDefinition=td_arn)
    validate_http_status('describe_task_definition', response)
    if len(response['taskDefinition']['containerDefinitions']) > 1:
        return None

    return response['taskDefinition']['containerDefinitions'][0]['image']


def deregister_task(ecs_client, td_arn):
    """
    """

    response = ecs_client.deregister_task_definition(taskDefinition=td_arn)
    validate_http_status('derigester_task_definition', response)
    print response['taskDefinition']['status']


# Service functions


def gather_all_services_for_cluster(ecs_client, cluster):
    """
    """

    # Adjust to our ECS naming convention
    if cluster not in TASKS_SUFFIX_DICT:
        raise Exception("gather_task_definitions called with invalid cluster name {}".format(cluster))

    response = ecs_client.list_services(cluster=cluster)
    validate_http_status('gather_all_services_for_cluster', response)

    service_list = []
    while True:
        arn_list = response['serviceArns']
        for arn in arn_list:
            service_list.append(arn)

        if 'nextToken' not in response:
            break

        response = ecs_client.list_services(cluster=cluster, nextToken=response['nextToken'])
        validate_http_status('gather_all_services_for_cluster', response)

    return service_list


# Garbage collect task definitions and their images


def garbage_collect_ecs(service, cluster):
    """
    Garbage collect Task Definitions revisions and their associated ECR images.

    :param str service: Name of the getTalent service.
    :param str cluster: name of the cluster to inspect.
    """

    # Adjust to our ECS naming convention
    if cluster not in SERVICES_SUFFIX_DICT:
        raise Exception("gather_task_definitions called with invalid cluster name {}".format(cluster))
    service_name = service + SERVICES_SUFFIX_DICT[cluster]

    ecs_client = boto3.client('ecs')

    # Find the currently running task definition
    response = ecs_client.describe_services(cluster=cluster, services=[ service_name ])
    validate_http_status('describe_services', response)
    if len(response['services']) != 1:
        raise Exception("garbage_collect_ecs: More than one service returned for {}".format(service_name))
    current_td = response['services'][0]['taskDefinition']
    current_image = task_definition_image(ecs_client, current_td)

    print "Currently Running TD: {}".format(current_td)

    # Get a list of all ACTIVE task definitions
    td_arn_list = gather_task_definitions(ecs_client, service, cluster)

    # Remove the task definition attached to the currently active service
    print "Found {} task definitions.".format(len(td_arn_list))
    if current_td in td_arn_list:
        print "Found current TD {} for service {}".format(current_td, service_name)
        td_arn_list.remove(current_td)
        print "List now has {} tds.".format(len(td_arn_list))
    else:
        print "WARNING: Currently running task definition {} for {} not found in Task Definition list.".format(current_td, service_name)

    # Cull the newest revisions that we want to keep out of the list
    for arn in td_arn_list:
        print arn
    print
    count = 0
    while count < GC_THRESHOLD:
        del td_arn_list[0] 
        count += 1
    for arn in td_arn_list:
        print arn

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
        print "DELETE {}".format(arn)

    print
    # Remove the images from our list, unless the current service uses it
    for image in image_delete_list:
        if image == current_image:
            print "WARNING: image {} in use by task {}. Not removed.".format(image, td_arn)
        else:
            print "DELETE {}".format(image)

    # TODO: go through all images and remove any dangling ones (those not attached to a task definition)

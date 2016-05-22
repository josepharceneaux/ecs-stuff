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

# How many previous Task Definitions (and related ECR images) to keep, including the currently running one
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


# Task Definition functions


def gather_task_definitions(service, cluster):
    """
    Collect all task definitions for getTalent service in a cluster.

    :param str service: Name of the getTalent service.
    :param str cluster: name of the cluster to inspect.
    """

    # Adjust to our ECS naming convention
    if cluster not in TASKS_SUFFIX_DICT:
        raise Exception("gather_task_definitions called with invalid cluster name {}".format(cluster))
    service = service + TASKS_SUFFIX_DICT[cluster]

    ecs_client = boto3.client('ecs')

    response = ecs_client.list_task_definitions(familyPrefix=service, status='ACTIVE', sort='DESC')
    validate_http_status('list_task_definitions', response)

    td_list = []
    while True:

        arn_list = response['taskDefinitionArns']
        for arn in arn_list:
            # print arn
            td_list.append(arn)

        if 'nextToken' not in response:
            break

        response = ecs_client.list_task_definitions(familyPrefix=service, status='ACTIVE', sort='DESC', )
        validate_http_status('list_task_definitions', response, nextToken=response['nextToken'])

    return td_list


def garbage_collect_ecs(service, cluster):
    """
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

    print "Currently Running TD: {}".format(current_td)

    # Get a list of all ACTIVE task definitions
    td_arn_list = gather_task_definitions(service, cluster)

    # Remove the task definition attached to the currently active service
    print "Found {} task definitions.".format(len(td_arn_list))
    if current_td in td_arn_list:
        print "Found current TD {} for service {}".format(current_td, service_name)
        td_arn_list.remove(current_td)
        print "List now has {} tds.".format(len(td_arn_list))
    else:
        print "WARNING: Currently running task definition {} for {} not found in Task Definition list.".format(current_td, service_name)

    # Prune the newest revisions that we want to keep
    for arn in td_arn_list:
        print arn

    # Now go through the remaining list and remove the ECR image and task definition

# Scripts

Scripts which are run manually, or by processes such as Jenkins. Jenkins builds on the `develop` branch push the container images built to the AWS repository,
creates a new task definition using the image, and restarts the service. An image running on `staging` can be promoted to production with the `move-stage-to-prod.py` script
described below.

## **__ecs_task_update.py__**

Intended to be run by the script ```push_containers.py```, which is run by Jenkins, it essentially restarts a service pointing at a recent build image. This is done tagging the
docker image in our AWS repository, building a task definition using that image, and restarting the sevice. It can be run on either staging or production, and restarting the
service is optional. It is invokded from the Jenkins script like this:

```
python scripts/ecs_task_update.py ${app} ${timestamp_tag} stage restart
```

## **__move-stage-to-prod.py__**

This script updates production to use the docker image currently running on staging. So, for example, if the most recent build is running on staging with a tag of **built-at-2016-05-09-17-37-01** production can be upgraded to use this image with:

```
python move-stage-to-prod.py candidate-service built-at-2016-05-09-17-37-01
```

Note that this script relies on strict naming conventions for ECS task definitions and services.

## **__scan-cluster.py__**

Scan an ECS cluster to describe the services and tasks currently running. Syntax is:

```
python scan-cluster.py [ stage | prod ]
```

It's output (per service) looks like:

```
candidate-service-svc ACTIVE Deployments: 1
Task: Family: candidate-service-td Revision: 18 Status: ACTIVE
Image: 528222547498.dkr.ecr.us-east-1.amazonaws.com/gettalent/candidate-service:built-at-2016-05-09-17-37-01
CPU: 1024 Memory 1500: 
```

## **__scan-candidates.py__**

Scan a database for inconsistencies between ```candidate``` and ```talent_pool``` entries. If ```--stage``` or ```--prod``` options are not specified, it uses the database locator:

```
mysql://talent_web:s!loc976892@localhost/talent_local
```

Otherwise the password for staging or production password must be provided as in:

```
scan-candidates.py --stage password
```

## **__add-column.py__**

Adds a column to a database table. Deprecated - use the service [migration system](https://github.com/gettalent/talent-flask-services/wiki/Database-Migrations-on-the-Cheap) instead.

__author__ = 'ufarooqi'

import json
import requests
from flask import request
from flask_restful import Resource
from dateutil import parser
from sqlalchemy import and_
from candidate_pool_service.candidate_pool_app.talent_pools_pipelines_utilities import TALENT_PIPELINE_SEARCH_PARAMS
from candidate_pool_service.common.utils.validators import is_number
from candidate_pool_service.common.models.talent_pools_pipelines import *
from candidate_pool_service.common.models.smartlist import Smartlist
from candidate_pool_service.common.utils.auth_utils import require_oauth, require_all_roles
from candidate_pool_service.common.routes import CandidateApiUrl
from candidate_pool_service.common.error_handling import *


class TalentPipelineApi(Resource):

    # Access token decorator
    decorators = [require_oauth]

    @require_all_roles('CAN_GET_TALENT_PIPELINES')
    def get(self, **kwargs):
        """
        GET /talent-pipelines/<id>      Fetch talent-pipeline object
        GET /talent-pipelines           Fetch all talent-pipelines objects of domain of logged-in user

        :return A dictionary containing talent-pipeline's basic info or a dictionary containing all talent-pipelines of
        a domain

        :rtype: dict
        """

        talent_pipeline_id = kwargs.get('id')

        if talent_pipeline_id:
            talent_pipeline = TalentPipeline.query.get(talent_pipeline_id)

            if not talent_pipeline:
                raise NotFoundError(error_message="Talent pipeline with id %s doesn't exist in database" %
                                                  talent_pipeline_id)

            if talent_pipeline.user.domain_id != request.user.domain_id:
                raise ForbiddenError(error_message="Logged-in user and talent_pipeline belong to different domain")

            return {
                'talent_pipeline': {
                    'id': talent_pipeline.id,
                    'name': talent_pipeline.name,
                    'description': talent_pipeline.description,
                    'user_id': talent_pipeline.owner_user_id,
                    'positions': talent_pipeline.positions,
                    'search_params': json.loads(talent_pipeline.search_params) if talent_pipeline.search_params else None,
                    'talent_pool_id': talent_pipeline.talent_pool_id,
                    'date_needed': str(talent_pipeline.date_needed),
                    'added_time': str(talent_pipeline.added_time),
                    'updated_time': str(talent_pipeline.updated_time)
                }
            }
        else:
            talent_pipelines = TalentPipeline.query.join(TalentPipeline.user).filter(User.domain_id ==
                                                                                     request.user.domain_id).all()
            return {
                'talent_pipelines': [
                    {
                        'id': talent_pipeline.id,
                        'name': talent_pipeline.name,
                        'description': talent_pipeline.description,
                        'user_id': talent_pipeline.owner_user_id,
                        'positions': talent_pipeline.positions,
                        'search_params': json.loads(talent_pipeline.search_params) if talent_pipeline.search_params else None,
                        'talent_pool_id': talent_pipeline.talent_pool_id,
                        'date_needed': str(talent_pipeline.date_needed),
                        'added_time': str(talent_pipeline.added_time),
                        'updated_time': str(talent_pipeline.updated_time)

                    } for talent_pipeline in talent_pipelines
                ]
            }

    @require_all_roles('CAN_DELETE_TALENT_PIPELINES')
    def delete(self, **kwargs):
        """
        DELETE /talent-pipelines/<id>  Remove talent-pipeline from Database

        :return A dictionary containing deleted talent-pipeline's id

        :rtype: dict
        """

        talent_pipeline_id = kwargs.get('id')

        if not talent_pipeline_id:
            raise InvalidUsage(error_message="A valid talent_pipeline_id should be provided")

        talent_pipeline = TalentPipeline.query.get(talent_pipeline_id)
        if not talent_pipeline:
            raise NotFoundError(error_message="Talent pipeline with id %s doesn't exist in database" %
                                              talent_pipeline_id)

        if talent_pipeline.user.domain_id != request.user.domain_id:
            raise ForbiddenError(error_message="Logged-in user and talent_pipeline belong to different domain")

        talent_pipeline.delete()

        return {
            'talent_pipeline': {'id': talent_pipeline.id}
        }

    @require_all_roles('CAN_ADD_TALENT_PIPELINES')
    def post(self, **kwargs):
        """
        POST /talent-pipelines  Add new talent-pipelines to Database
        input: {'talent_pipelines': [talent_pipeline_dict1, talent_pipeline_dict2, talent_pipeline_dict3, ... ]}

        Take a JSON dictionary containing array of TalentPipeline dictionaries
        A single talent-pipelines dict must contain pipelines's name, date_needed, talent_pool_id

        :return A dictionary containing ids of added talent-pipelines

        :rtype: dict
        """

        posted_data = request.get_json(silent=True)
        if not posted_data or 'talent_pipelines' not in posted_data:
            raise InvalidUsage(error_message="Request body is empty or not provided")

        # Save user object(s)
        talent_pipelines = posted_data['talent_pipelines']

        # TalentPipeline object(s) must be in a list
        if not isinstance(talent_pipelines, list):
            raise InvalidUsage(error_message="Request body is not properly formatted")

        talent_pipeline_objects = []
        for talent_pipeline in talent_pipelines:

            name = talent_pipeline.get('name', '')
            description = talent_pipeline.get('description', '')
            positions = talent_pipeline.get('positions', 1)
            date_needed = talent_pipeline.get('date_needed', '')
            talent_pool_id = talent_pipeline.get('talent_pool_id', '')
            search_params = talent_pipeline.get('search_params', dict())

            if not name or not date_needed or not talent_pool_id:
                raise InvalidUsage(error_message="A valid name, date_needed, talent_pool_id should be provided to "
                                                 "create a new talent-pipeline")

            if TalentPipeline.query.join(TalentPipeline.user).filter(and_(TalentPipeline.name == name, User.
                    domain_id == request.user.domain_id)).first():
                raise InvalidUsage(error_message="Talent pipeline with name %s already exists in domain %s" %
                                                 (name, request.user.domain_id))

            try:
                parser.parse(date_needed)
            except Exception as e:
                raise InvalidUsage(error_message="Date_needed is not valid as: %s" % e.message)

            if parser.parse(date_needed) < datetime.datetime.utcnow():
                raise InvalidUsage(error_message="Date_needed %s cannot be before current date" % date_needed)

            if not is_number(positions) or not int(positions) > 0:
                raise InvalidUsage(error_message="Number of positions should be integer and greater than zero")

            if not is_number(talent_pool_id):
                raise InvalidUsage(error_message="talent_pool_id should be an integer")

            talent_pool_id = int(talent_pool_id)
            talent_pool = TalentPool.query.get(talent_pool_id)
            if not talent_pool:
                raise NotFoundError(error_message="Talent pool with id %s doesn't exist in database" % talent_pool_id)

            if talent_pool.domain_id != request.user.domain_id:
                raise ForbiddenError(error_message="Logged-in user and given talent-pool belong to different domain")

            if search_params:
                if not isinstance(search_params, dict):
                    raise InvalidUsage(error_message="search_params is not provided in valid format")

                # Put into params dict
                for key in search_params:
                    if key not in TALENT_PIPELINE_SEARCH_PARAMS and not key.startswith('cf-'):
                        raise NotFoundError(error_message="Key[%s] is invalid" % key)

            search_params = json.dumps(search_params) if search_params else None

            talent_pipeline = TalentPipeline(name=name, description=description, positions=positions,
                                             date_needed=date_needed, owner_user_id=request.user.id,
                                             talent_pool_id=talent_pool_id, search_params=search_params)

            db.session.add(talent_pipeline)
            talent_pipeline_objects.append(talent_pipeline)

        db.session.commit()

        return {
            'talent_pipelines': [talent_pipeline_object.id for talent_pipeline_object in talent_pipeline_objects]
        }

    @require_all_roles('CAN_EDIT_TALENT_PIPELINES')
    def put(self, **kwargs):
        """
        PUT /talent-pipelines/<id>  Edit existing talent-pipeline

        Take a JSON dictionary containing TalentPipeline dictionary

        :return A dictionary containing id of edited talent-pipeline

        :rtype: dict
        """

        talent_pipeline_id = kwargs.get('id')

        if not talent_pipeline_id:
            raise InvalidUsage(error_message="A valid talent_pipeline_id should be provided")

        talent_pipeline = TalentPipeline.query.get(talent_pipeline_id)
        if not talent_pipeline:
            raise NotFoundError(error_message="Talent pipeline with id %s doesn't exist in database" %
                                              talent_pipeline_id)

        if talent_pipeline.user.domain_id != request.user.domain_id:
            raise ForbiddenError(error_message="Logged-in user and talent_pipeline belong to different domain")

        posted_data = request.get_json(silent=True)
        if not posted_data or 'talent_pipeline' not in posted_data:
            raise InvalidUsage(error_message="Request body is empty or not provided")
        posted_data = posted_data['talent_pipeline']

        name = posted_data.get('name', '')
        description = posted_data.get('description', '')
        positions = posted_data.get('positions', '')
        date_needed = posted_data.get('date_needed', '')
        talent_pool_id = posted_data.get('talent_pool_id', '')
        search_params = posted_data.get('search_params', dict())

        if name:
            if TalentPipeline.query.join(TalentPipeline.user).filter(
                    and_(TalentPipeline.name == name, User.domain_id == request.user.domain_id)).first():
                raise InvalidUsage(error_message="Talent pipeline with name %s already exists in domain %s" %
                                                 (name, request.user.domain_id))
            talent_pipeline.name = name

        if date_needed:
            try:
                parser.parse(date_needed)
            except Exception as e:
                raise InvalidUsage(error_message="Date_needed is not valid as: %s" % e.message)

            if parser.parse(date_needed) < datetime.datetime.utcnow():
                raise InvalidUsage(error_message="Date_needed %s cannot be before current date" % date_needed)

            talent_pipeline.date_needed = date_needed

        if positions:
            if not is_number(positions) or not int(positions) > 0:
                raise InvalidUsage(error_message="Number of positions should be integer and greater than zero")

            talent_pipeline.positions = positions

        if description:
            talent_pipeline.description = description

        if talent_pool_id:

            if not is_number(talent_pool_id):
                raise InvalidUsage(error_message="talent_pool_id should be an integer")

            talent_pool_id = int(talent_pool_id)
            talent_pool = TalentPool.query.get(talent_pool_id)
            if not talent_pool:
                raise NotFoundError(error_message="Talent pool with id %s doesn't exist in database" % talent_pool_id)

            if talent_pool.domain_id != request.user.domain_id:
                raise ForbiddenError(error_message="Logged-in user and given talent-pool belong to different domain")

            talent_pipeline.talent_pool_id = talent_pool_id

        if search_params:
            if not isinstance(search_params, dict):
                raise InvalidUsage(error_message="search_params is not provided in valid format")

            # Put into params dict
            for key in search_params:
                if key not in TALENT_PIPELINE_SEARCH_PARAMS and not key.startswith('cf-'):
                    raise NotFoundError(error_message="Key[%s] is invalid" % key)

            talent_pipeline.search_params = json.dumps(search_params)

        db.session.commit()

        return {
            'talent_pipeline': {'id': talent_pipeline.id}
        }


class TalentPipelineSmartListApi(Resource):

    # Access token decorator
    decorators = [require_oauth]

    @require_all_roles('CAN_GET_TALENT_PIPELINE_SMART_LISTS')
    def get(self, **kwargs):
        """
        GET /talent-pipeline/<id>/smart_lists   Fetch all smart_lists of a talent_pipeline

        :return A dictionary containing smart_list objects of a talent_pipeline

        :rtype: dict
        """

        talent_pipeline_id = kwargs.get('id')

        talent_pipeline = TalentPipeline.query.get(talent_pipeline_id)

        if not talent_pipeline:
            raise NotFoundError(error_message="Talent pipeline with id %s doesn't exist in database" %
                                              talent_pipeline_id)

        if talent_pipeline.user.domain_id != request.user.domain_id:
            raise ForbiddenError(error_message="Logged-in user and talent_pipeline belong to different domain")

        smart_lists = Smartlist.query.filter_by(talent_pipeline_id=talent_pipeline_id).all()

        return {
            'smart_lists': [
                {
                    'name': smart_list.name,
                    'user_id': smart_list.user_id,
                    'is_hidden': smart_list.is_hidden,
                    'search_params': json.loads(smart_list.search_params) if smart_list.search_params else None

                }
                for smart_list in smart_lists
            ]
        }

    @require_all_roles('CAN_ADD_TALENT_PIPELINE_SMART_LISTS')
    def post(self, **kwargs):
        """
        POST /talent-pipeline/<id>/smart_lists   Add smart_lists to a talent_pipeline

        Take a JSON dictionary containing smart_list_ids

        :return A dictionary containing smart_list_ids successfully added to talent_pipeline

        :rtype: dict
        """

        talent_pipeline_id = kwargs.get('id')

        talent_pipeline = TalentPipeline.query.get(talent_pipeline_id)

        if not talent_pipeline:
            raise NotFoundError(error_message="Talent pipeline with id %s doesn't exist in database" %
                                              talent_pipeline_id)

        posted_data = request.get_json(silent=True)
        if not posted_data or 'smart_list_ids' not in posted_data:
            raise InvalidUsage(error_message="Request body is empty or not provided")

        # Save user object(s)
        smart_list_ids = posted_data['smart_list_ids']

        # Talent_pool object(s) must be in a list
        if not isinstance(smart_list_ids, list):
            raise InvalidUsage(error_message="Request body is not properly formatted")

        if talent_pipeline.user.domain_id != request.user.domain_id:
            raise ForbiddenError(error_message="Logged-in user and talent_pipeline belong to different domain")

        for smart_list_id in smart_list_ids:

            if not is_number(smart_list_id):
                raise InvalidUsage('Smart List id %s should be an integer' % smart_list_id)
            else:
                smart_list_id = int(smart_list_id)

            smart_list = Smartlist.query.get(smart_list_id)

            if smart_list.user.domain_id != talent_pipeline.user.domain_id:
                raise ForbiddenError(error_message="Smart list %s and Talent pipeline %s belong to different domain"
                                                   % (smart_list_id, talent_pipeline_id))

            if smart_list.talent_pipeline_id == talent_pipeline_id:
                raise InvalidUsage(error_message="Smart List %s already belongs to Talent Pipeline %s"
                                                 % (smart_list.name, talent_pipeline_id))

            if smart_list.talent_pipeline_id:
                raise ForbiddenError(error_message="smart_list %s is already assigned to talent_pipeline %s" %
                                                   (smart_list.name, smart_list.talent_pipeline_id))

            smart_list.talent_pipeline_id = talent_pipeline_id

        db.session.commit()

        return {
            'smart_list_ids': [int(smart_list_id) for smart_list_id in smart_list_ids]
        }

    @require_all_roles('CAN_DELETE_TALENT_PIPELINE_SMART_LISTS')
    def delete(self, **kwargs):
        """
        DELETE /talent-pipeline/<id>/smart_lists   Remove smart_lists from a talent_pipeline

        Take a JSON dictionary containing smart_list_ids

        :return A dictionary containing smart_list_ids successfully removed from a talent_pipeline

        :rtype: dict
        """

        talent_pipeline_id = kwargs.get('id')

        talent_pipeline = TalentPipeline.query.get(talent_pipeline_id)

        if not talent_pipeline:
            raise NotFoundError(error_message="Talent pipeline with id %s doesn't exist in database" %
                                              talent_pipeline_id)

        posted_data = request.get_json(silent=True)
        if not posted_data or 'smart_list_ids' not in posted_data:
            raise InvalidUsage(error_message="Request body is empty or not provided")

        # Save user object(s)
        smart_list_ids = posted_data['smart_list_ids']

        # Talent_pool object(s) must be in a list
        if not isinstance(smart_list_ids, list):
            raise InvalidUsage(error_message="Request body is not properly formatted")

        if talent_pipeline.user.domain_id != request.user.domain_id:
            raise ForbiddenError(error_message="Logged-in user and talent_pipeline belong to different domain")

        for smart_list_id in smart_list_ids:

            if not is_number(smart_list_id):
                raise InvalidUsage('Smart List id %s should be an integer' % smart_list_id)
            else:
                smart_list_id = int(smart_list_id)

            smart_list = Smartlist.query.get(smart_list_id)

            if smart_list.talent_pipeline_id != talent_pipeline_id:
                raise ForbiddenError(error_message="smart_list %s doesn't belong to talent_pipeline %s" %
                                                   (smart_list.name, talent_pipeline_id))

            smart_list.talent_pipeline_id = None

        db.session.commit()

        return {
            'smart_list_ids': [int(smart_list_id) for smart_list_id in smart_list_ids]
        }


class TalentPipelineCandidates(Resource):

    # Access token decorator
    decorators = [require_oauth]

    @require_all_roles('CAN_GET_TALENT_PIPELINE_CANDIDATES')
    def get(self, **kwargs):
        """
        GET /talent-pipeline/<id>/candidates  Fetch all candidates of a talent-pipeline
        Query String: {'fields': 'id,email', 'sort_by': 'match' 'limit':10, 'page': 2}
        :return A dictionary containing list of candidates belonging to a talent-pipeline

        :rtype: dict
        """

        talent_pipeline_id = kwargs.get('id')

        talent_pipeline = TalentPipeline.query.get(talent_pipeline_id)

        if not talent_pipeline:
            raise NotFoundError(error_message="Talent pipeline with id %s doesn't exist in database" %
                                              talent_pipeline_id)

        if talent_pipeline.user.domain_id != request.user.domain_id:
            raise ForbiddenError(error_message="Logged-in user and talent_pipeline belong to different domain")

        # Get all smart_lists and dumb_lists of a talent-pipeline
        smart_lists = Smartlist.query.filter_by(talent_pipeline_id=talent_pipeline_id).all()

        search_params, dumb_lists = [], []

        try:
            if talent_pipeline.search_params and json.loads(talent_pipeline.search_params):
                search_params.append(json.loads(talent_pipeline.search_params))
            for smart_list in smart_lists:
                if smart_list.search_params and json.loads(smart_list.search_params):
                    search_params.append(json.loads(smart_list.search_params))
                else:
                    dumb_lists.append(str(smart_list.id))

        except Exception as e:
            raise InvalidUsage(error_message="Search params of talent-pipeline or its smart-lists are in bad format "
                                             "because: %s" % e.message)

        headers = {'Authorization': request.oauth_token, 'Content-Type': 'application/json'}

        request_params = dict()

        request_params['talent_pool_id'] = talent_pipeline.talent_pool_id
        request_params['fields'] = request.args.get('fields', '')
        request_params['sort_by'] = request.args.get('sort_by', '')
        request_params['limit'] = request.args.get('limit', '')
        request_params['page'] = request.args.get('page', '')
        request_params['dumb_list_ids'] = ','.join(dumb_lists) if dumb_lists else None
        request_params['search_params'] = json.dumps(search_params) if search_params else None

        request_params = dict((k, v) for k, v in request_params.iteritems() if v)

        # Query Candidate Search API to get all candidates of a given talent-pipeline
        try:
            response = requests.get(CandidateApiUrl.CANDIDATE_SEARCH_URI, headers=headers, params=request_params)
            if response.ok:
                return response.json()
            else:
                raise Exception("Status Code: %s, Response: %s" % (response.status_code, response.json()))
        except Exception as e:
            raise InvalidUsage(error_message="Couldn't get candidates from candidates search service because: "
                                             "%s" % e.message)



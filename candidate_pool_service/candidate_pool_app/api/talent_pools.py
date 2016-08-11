
__author__ = 'ufarooqi'

import hashlib
import requests
from flask import Blueprint
from flask_restful import Resource
from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError
from candidate_pool_service.common.error_handling import *
from candidate_pool_service.common.talent_api import TalentApi
from candidate_pool_service.common.routes import CandidateApiUrl
from candidate_pool_service.common.routes import CandidatePoolApi
from candidate_pool_service.common.utils.validators import is_number
from candidate_pool_service.common.utils.api_utils import ApiResponse, generate_pagination_headers
from candidate_pool_service.common.models.talent_pools_pipelines import *
from candidate_pool_service.common.utils.api_utils import DEFAULT_PAGE, DEFAULT_PAGE_SIZE
from candidate_pool_service.common.utils.auth_utils import require_oauth, require_all_permissions
from candidate_pool_service.candidate_pool_app.talent_pools_pipelines_utilities import (
    get_stats_generic_function, update_smartlist_stats, update_talent_pipeline_stats,
    update_talent_pool_stats, get_candidates_of_talent_pool)
from candidate_pool_service.common.utils.handy_functions import random_word
from candidate_pool_service.common.models.user import Permission

talent_pool_blueprint = Blueprint('talent_pool_api', __name__)


class TalentPoolApi(Resource):

    # Access token decorator
    decorators = [require_oauth()]

    # 'SELF' is for readability. It means this endpoint will be accessible to any user
    @require_all_permissions(Permission.PermissionNames.CAN_GET_TALENT_POOLS)
    def get(self, **kwargs):
        """
        GET /talent-pools/<id>          Fetch talent-pool object
        GET /talent-pools               Fetch all talent-pool objects of domain of logged-in user

        :return A dictionary containing talent-pool basic info or a dictionary containing all talent-pools of a domain
        :rtype: dict
        """

        talent_pool_id = kwargs.get('id')

        # Getting a single talent-pool
        if talent_pool_id:
            talent_pool = TalentPool.query.get(talent_pool_id)

            if not talent_pool:
                raise NotFoundError("Talent pool with id {} doesn't exist in database".format(talent_pool_id))

            if request.user.role.name != 'TALENT_ADMIN' and talent_pool.domain_id != request.user.domain_id:
                raise ForbiddenError("User {} is not authorized to get talent-pool's info".format(request.user.id))

            talent_pool_group = TalentPoolGroup.query.filter_by(user_group_id=request.user.user_group_id,
                                                                talent_pool_id=talent_pool_id).all()
            if request.user.role.name == 'USER' and not talent_pool_group:
                raise ForbiddenError("User {} doesn't have appropriate permissions to get "
                                     "talent-pools's info".format(request.user.id))
            return {
                'talent_pool': {
                    'id': talent_pool.id,
                    'name': talent_pool.name,
                    'description': talent_pool.description,
                    'domain_id': talent_pool.domain_id,
                    'user_id': talent_pool.user_id,
                    'added_time': talent_pool.added_time.isoformat(),
                    'updated_time': talent_pool.updated_time.isoformat()
                }
            }
        # Getting all talent-pools of logged-in user's domain
        else:
            talent_pools = TalentPool.query.filter_by(domain_id=request.user.domain_id).all()
            return {
                'talent_pools': [
                    {
                        'id': talent_pool.id,
                        'name': talent_pool.name,
                        'description': talent_pool.description,
                        'user_id': talent_pool.user_id,
                        'added_time': talent_pool.added_time.isoformat(),
                        'updated_time': talent_pool.updated_time.isoformat(),
                        'accessible_to_user_group_ids': [talent_pool_group.user_group_id for talent_pool_group in
                                                         TalentPoolGroup.query.filter_by(
                                                                 talent_pool_id=talent_pool.id
                                                         ).all()]
                    } for talent_pool in talent_pools
                ]
            }

    @require_all_permissions(Permission.PermissionNames.CAN_EDIT_TALENT_POOLS)
    def put(self, **kwargs):
        """
        PUT /talent-pools/<id>      Modify an already existing talent-pool
        input: {'name': 'facebook-recruiting', 'description': ''}

        :return {'talent_pool': {'id': talent_pool_id}}
        :rtype: dict
        """

        talent_pool_id = kwargs.get('id')
        if not talent_pool_id:
            raise InvalidUsage("A valid talent_pool_id should be provided")

        talent_pool = TalentPool.query.get(talent_pool_id)
        if not talent_pool:
            raise NotFoundError("Talent pool with id {} doesn't exist in database".format(talent_pool_id))

        posted_data = request.get_json(silent=True)
        if not posted_data or 'talent_pool' not in posted_data:
            raise InvalidUsage("Request body is empty or not provided")

        posted_data = posted_data['talent_pool']

        # posted_data must be in a dict
        if not isinstance(posted_data, dict):
            raise InvalidUsage("Request body is not properly formatted")

        if request.user.role.name != 'TALENT_ADMIN' and request.user.domain_id != talent_pool.domain_id:
            raise ForbiddenError("User {} is not authorized to edit talent-pool's info".format(request.user.id))

        name = posted_data.get('name')
        description = posted_data.get('description')

        if not name and not description:
            raise InvalidUsage("Neither modified name nor description is provided")

        if name and not TalentPool.query.filter_by(name=name, domain_id=talent_pool.domain_id).all():
            talent_pool.name = name
        elif name:
            raise InvalidUsage("Talent pool {} already exists in domain {}".format(name, talent_pool.domain_id))

        if description:
            talent_pool.description = description

        db.session.commit()

        return {
            'talent_pool': {'id': talent_pool.id}
        }

    @require_all_permissions(Permission.PermissionNames.CAN_DELETE_TALENT_POOLS)
    def delete(self, **kwargs):
        """
        DELETE /talent-pools/<id>      Delete an already existing talent-pool
        :return {'delete_talent_pool': {'id': talent_pool_id}}
        :rtype: dict
        """

        talent_pool_id = kwargs.get('id')
        if not talent_pool_id:
            raise InvalidUsage("A valid talent_pool_id should be provided")

        talent_pool = TalentPool.query.get(talent_pool_id)
        if not talent_pool:
            raise NotFoundError("Talent pool with id {} doesn't exist in database".format(talent_pool_id))

        if request.user.role.name != 'TALENT_ADMIN' and request.user.domain_id != talent_pool.domain_id:
            raise ForbiddenError("User {} is not authorized to delete a talent-pool".format(request.user.id))

        talent_pool_candidate_ids = map(lambda talent_pool_candidate: talent_pool_candidate[0],
                                        TalentPoolCandidate.query.with_entities(TalentPoolCandidate.candidate_id).
                                        filter_by(talent_pool_id=talent_pool_id).all())
        talent_pool.delete()

        if talent_pool_candidate_ids:
            try:
                # Update Candidate Documents in Amazon Cloud Search
                headers = {'Authorization': request.oauth_token, 'Content-Type': 'application/json'}
                response = requests.post(CandidateApiUrl.CANDIDATES_DOCUMENTS_URI, headers=headers,
                                         data=json.dumps({'candidate_ids': talent_pool_candidate_ids}))

                if response.status_code != 204:
                    raise Exception("Status Code: {} Response: {}".format(response.status_code, response.json()))

            except Exception as e:
                raise InvalidUsage("Couldn't update Candidate Documents in Amazon Cloud "
                                   "Search. Because: {}".format(e.message))

        return {
            'talent_pool': {'id': talent_pool.id}
        }

    @require_all_permissions(Permission.PermissionNames.CAN_ADD_TALENT_POOLS)
    def post(self, **kwargs):
        """
        POST /talent-pools    Create new empty talent pools
        input: {'talent_pools': [talent_pool_dict1, talent_pool_dict2, talent_pool_dict3, ... ]}

        Take a JSON dictionary containing array of TalentPool dictionaries
        A single talent-pool dict must contain pool's name

        :return A dictionary containing talent_pools_ids
        :rtype: dict
        """

        posted_data = request.get_json(silent=True)
        if not posted_data or 'talent_pools' not in posted_data:
            raise InvalidUsage("Request body is empty or not provided")

        # Save user object(s)
        talent_pools = posted_data['talent_pools']

        # Talent_pool object(s) must be in a list
        if not isinstance(talent_pools, list):
            raise InvalidUsage("Request body is not properly formatted")

        talent_pool_objects = []
        for talent_pool in talent_pools:

            name = talent_pool.get('name', '').strip()
            description = talent_pool.get('description', '').strip()
            user_object = User.query.get(talent_pool.get('user_id', request.user.id))
            if not user_object:
                raise InvalidUsage("User with id {} doesn't exist in Database".format(user_object.id))

            if request.user.role.name != 'TALENT_ADMIN' and user_object.domain_id != request.user.domain_id:
                raise UnauthorizedError("User {} doesn't have appropriate permission to "
                                        "add TalentPool".format(request.user.id))

            if not name:
                raise InvalidUsage("A valid name should be provided to create a talent-pool")

            if name and TalentPool.query.filter_by(name=name, domain_id=user_object.domain_id).all():
                raise InvalidUsage("Talent pool '{}' already exists in domain {}".format(name, user_object.domain_id))

            # Add TalentPool
            talent_pool_object = TalentPool(name=name, description=description, domain_id=user_object.domain_id,
                                            user_id=user_object.id)
            talent_pool_objects.append(talent_pool_object)
            db.session.add(talent_pool_object)
            db.session.flush()

            # Add TalentPoolGroup to associate new TalentPool with existing UserGroup
            db.session.add(TalentPoolGroup(talent_pool_id=talent_pool_object.id,
                                           user_group_id=user_object.user_group_id))

        db.session.commit()

        for talent_pool in talent_pool_objects:
            hash = hashlib.md5()
            hash.update(str(talent_pool.id))
            talent_pool.simple_hash = hash.hexdigest()[:8]
            pool_saved = False
            while not pool_saved:
                try:
                    db.session.add(talent_pool)
                    db.session.commit()
                    pool_saved = True
                except IntegrityError:
                    hash.update(random_word(8))

        return {'talent_pools': [talent_pool_object.id for talent_pool_object in talent_pool_objects]}


class TalentPoolGroupApi(Resource):

    # Access token decorator
    decorators = [require_oauth()]

    # 'SELF' is for readability. It means this endpoint will be accessible to any user
    @require_all_permissions(Permission.PermissionNames.CAN_GET_DOMAIN_GROUPS)
    def get(self, **kwargs):
        """
        GET /groups/<group_id>/talent_pools     Fetch all talent-pool objects of given user group

        :return A dictionary containing all talent-pools of a user group
        :rtype: dict
        """

        user_group_id = kwargs.get('group_id')
        user_group = UserGroup.query.get(user_group_id)

        if not user_group:
            raise NotFoundError("User group with id {} doesn't exist".format(user_group_id))

        if request.user.role.name != 'TALENT_ADMIN' and user_group.domain_id != request.user.domain_id:
            raise ForbiddenError("Logged-in user belongs to different domain as given user group")

        talent_pool_ids = [talent_pool_group.talent_pool_id for talent_pool_group in
                           TalentPoolGroup.query.filter_by(user_group_id=user_group_id).all()]

        talent_pools = TalentPool.query.filter(TalentPool.id.in_(talent_pool_ids)).all()
        return {
            'talent_pools': [
                {
                    'id': talent_pool.id,
                    'name': talent_pool.name,
                    'description': talent_pool.description,
                    'domain_id': talent_pool.domain_id,
                    'user_id': talent_pool.user_id

                } for talent_pool in talent_pools
            ]
        }

    @require_all_permissions(Permission.PermissionNames.CAN_EDIT_DOMAIN_GROUPS)
    def delete(self, **kwargs):
        """
        DELETE /groups/<group_id>/talent_pools   Remove given input of talent-pool ids from user group
        input: {'talent_pools': [talent_pool_id1, talent_pool_id2, talent_pool_id3, ... ]}

        :return A dictionary containing talent-pool ids which have been removed successfully
        :rtype: dict
        """
        user_group_id = kwargs.get('group_id')

        posted_data = request.get_json(silent=True)
        if not posted_data or 'talent_pools' not in posted_data:
            raise InvalidUsage("Request body is empty or not provided")

        # Save user object(s)
        talent_pool_ids = posted_data['talent_pools']

        # Talent_pool object(s) must be in a list
        if not isinstance(talent_pool_ids, list):
            raise InvalidUsage("Request body is not properly formatted")

        user_group = UserGroup.query.get(user_group_id)

        if not user_group:
            raise NotFoundError("User group with id {} doesn't exist".format(user_group_id))

        if request.user.role.name != 'TALENT_ADMIN' and request.user.domain_id != user_group.domain_id:
            raise ForbiddenError("Logged-in user and given user-group belong to different domains")

        for talent_pool_id in talent_pool_ids:

            if not is_number(talent_pool_id):
                raise InvalidUsage('Talent pool id {} should be an integer'.format(talent_pool_id))
            else:
                talent_pool_id = int(talent_pool_id)

            talent_pool_group = TalentPoolGroup.query.filter_by(user_group_id=user_group_id,
                                                                talent_pool_id=talent_pool_id).first()
            if not talent_pool_group:
                raise NotFoundError("Talent pool {} doesn't belong to group {}".format(talent_pool_id, user_group_id))
            else:
                db.session.delete(talent_pool_group)

        db.session.commit()

        return {'talent_pools': [int(talent_pool_id) for talent_pool_id in talent_pool_ids]}

    @require_all_permissions(Permission.PermissionNames.CAN_EDIT_DOMAIN_GROUPS)
    def post(self, **kwargs):
        """
        POST /groups/<group_id>/talent_pools   Add talent-pools to user_group
        input: {'talent_pools': [talent_pool_id1, talent_pool_id2, talent_pool_id3, ... ]}

        :return A dictionary containing talent-pool ids which have been added successfully
        :rtype: dict
        """

        user_group_id = kwargs.get('group_id')

        posted_data = request.get_json(silent=True)
        if not posted_data or 'talent_pools' not in posted_data:
            raise InvalidUsage("Request body is empty or not provided")

        # Save user object(s)
        talent_pool_ids = posted_data['talent_pools']

        # Talent_pool object(s) must be in a list
        if not isinstance(talent_pool_ids, list):
            raise InvalidUsage("Request body is not properly formatted")

        user_group = UserGroup.query.get(user_group_id)

        if not user_group:
            raise NotFoundError("User group with id {} doesn't exist".format(user_group_id))

        if request.user.role.name != 'TALENT_ADMIN' and request.user.domain_id != user_group.domain_id:
            raise ForbiddenError("Logged-in user and given user-group belong to different domains")

        for talent_pool_id in talent_pool_ids:

            if not is_number(talent_pool_id):
                raise InvalidUsage('Talent pool id {} should be an integer'.format(talent_pool_id))
            else:
                talent_pool_id = int(talent_pool_id)

            if TalentPoolGroup.query.filter_by(user_group_id=user_group_id, talent_pool_id=talent_pool_id).first():
                raise InvalidUsage("Talent pool {} already belongs to user group {}".format(talent_pool_id, user_group_id))

            talent_pool = TalentPool.query.get(talent_pool_id)
            if not talent_pool:
                raise NotFoundError("Talent pool {} doesn't exist in database".format(talent_pool_id))

            if user_group.domain_id != talent_pool.domain_id:
                raise ForbiddenError("Talent pool {} and user_group {} belong to different "
                                   "domain".format(talent_pool.name, user_group.name))

            db.session.add(TalentPoolGroup(talent_pool_id=talent_pool_id, user_group_id=user_group_id))

        db.session.commit()
        return {'added_talent_pools': [int(talent_pool_id) for talent_pool_id in talent_pool_ids]}


class TalentPoolCandidateApi(Resource):

    # Access token decorator
    decorators = [require_oauth()]

    @require_all_permissions(Permission.PermissionNames.CAN_GET_CANDIDATES)
    def get(self, **kwargs):
        """
        GET /talent-pools/<id>/candidates  Fetch Candidate Statistics of Talent-Pool

        :return A dictionary containing Candidate Statistics of a Talent Pool
        :rtype: dict
        """
        talent_pool_id = kwargs.get('id')
        talent_pool = TalentPool.query.get(talent_pool_id)

        if not talent_pool:
            raise NotFoundError("Talent pool with id {} doesn't exist in database".format(talent_pool_id))

        if request.user.role.name != 'TALENT_ADMIN' and talent_pool.domain_id != request.user.domain_id:
            raise ForbiddenError("Talent pool and logged in user belong to different domains")

        talent_pool_group = TalentPoolGroup.query.filter_by(user_group_id=request.user.user_group_id,
                                                            talent_pool_id=talent_pool_id).first()
        if request.user.role.name == 'USER' and not talent_pool_group:
            raise ForbiddenError("User {} doesn't have appropriate permissions to get "
                                 "candidates".format(request.user.id))

        request_params = dict()
        request_params['fields'] = request.args.get('fields', '')
        request_params['sort_by'] = request.args.get('sort_by', '')
        request_params['limit'] = request.args.get('limit', '')
        request_params['page'] = request.args.get('page', '')

        search_candidates_response = get_candidates_of_talent_pool(talent_pool, request.oauth_token, request_params)

        #  To be backwards-compatible, for now, we add talent_pool_candidates to top level dict
        search_candidates_response['talent_pool_candidates'] = {
            'name': talent_pool.name, 'total_found': search_candidates_response.get('total_found')}

        return search_candidates_response

    # 'SELF' is for readability. It means this endpoint will be accessible to any user
    @require_all_permissions(Permission.PermissionNames.CAN_ADD_CANDIDATES)
    def post(self, **kwargs):

        """
        POST /talent-pools/<id>/candidates   Add input candidates in talent-pool
        input: {'talent_pool_candidates': [talent_pool_candidate_id1, talent_pool_candidate_id2, ... ]}

        :return A dictionary containing candidate_ids which have been added successfully
        :rtype: dict
        """

        talent_pool_id = kwargs.get('id')

        posted_data = request.get_json(silent=True)
        if not posted_data or 'talent_pool_candidates' not in posted_data:
            raise InvalidUsage("Request body is empty or not provided")

        # Save user object(s)
        talent_pool_candidate_ids = posted_data['talent_pool_candidates']

        # Talent_pool object(s) must be in a list
        if not isinstance(talent_pool_candidate_ids, list):
            raise InvalidUsage("Request body is not properly formatted")

        talent_pool = TalentPool.query.get(talent_pool_id)

        if not talent_pool:
            raise NotFoundError("Talent pool with id {} doesn't exist in database".format(talent_pool_id))

        if request.user.role.name != 'TALENT_ADMIN' and talent_pool.domain_id != request.user.domain_id:
            raise ForbiddenError("Talent pool and logged-in user belong to different domains")

        talent_pool_group = TalentPoolGroup.query.filter_by(user_group_id=request.user.user_group_id,
                                                            talent_pool_id=talent_pool_id).first()
        if request.user.role.name == 'USER' and not talent_pool_group:
            raise ForbiddenError("User {} doesn't have appropriate permissions to add "
                                 "candidates".format(request.user.id))

        try:
            talent_pool_candidate_ids = [int(talent_pool_candidate_id) for talent_pool_candidate_id in
                                         talent_pool_candidate_ids]
        except:
            raise InvalidUsage("All candidate ids should be integer")

        # Candidates which already exist in a given talent-pool
        already_existing_candidates_in_talent_pool = TalentPoolCandidate.query.filter(and_(
            TalentPoolCandidate.talent_pool_id == talent_pool_id, TalentPoolCandidate.candidate_id.in_(
                talent_pool_candidate_ids))).all()

        # No candidate should already exist in a given talent-pool
        if len(already_existing_candidates_in_talent_pool) > 0:
            raise InvalidUsage("Candidate {} already exists in talent-pool {}".format(
                    already_existing_candidates_in_talent_pool[0].id, talent_pool_id))

        # Candidates with input candidate ids exist in database or not
        for talent_pool_candidate_id in talent_pool_candidate_ids:
            talent_pool_candidate = Candidate.query.get(talent_pool_candidate_id)
            if not talent_pool_candidate:
                raise NotFoundError("Candidate with id {} doesn't exist in database".format(talent_pool_candidate_id))

            if talent_pool_candidate.user.domain_id != talent_pool.domain_id:
                raise ForbiddenError("Talent Pool {} and Candidate {} belong to different domain".format(talent_pool.id, talent_pool_candidate.id))
            db.session.add(TalentPoolCandidate(talent_pool_id=talent_pool_id, candidate_id=talent_pool_candidate_id))

        db.session.commit()

        try:
            # Update Candidate Documents in Amazon Cloud Search
            headers = {'Authorization': request.oauth_token, 'Content-Type': 'application/json'}
            response = requests.post(CandidateApiUrl.CANDIDATES_DOCUMENTS_URI, headers=headers,
                                     data=json.dumps({'candidate_ids': talent_pool_candidate_ids}))

            if response.status_code != 204:
                raise Exception("Status Code: {} Response: {}".format(response.status_code, response.json()))

        except Exception as e:
            raise InvalidUsage("Couldn't update Candidate Documents in Amazon Cloud "
                               "Search. Because: {}".format(e.message))

        return {'added_talent_pool_candidates': [int(talent_pool_candidate_id) for talent_pool_candidate_id in
                                                 talent_pool_candidate_ids]}

    @require_all_permissions(Permission.PermissionNames.CAN_DELETE_CANDIDATES)
    def delete(self, **kwargs):
        """
        DELETE /talent-pools/<id>/candidates   Remove input candidates from talent-pool
        input: {'talent_pool_candidates': [talent_pool_candidate_id1, talent_pool_candidate_id2, ... ]}

        :return A dictionary containing candidate_ids which have been removed successfully
        :rtype: dict
        """

        talent_pool_id = kwargs.get('id')

        posted_data = request.get_json(silent=True)
        if not posted_data or 'talent_pool_candidates' not in posted_data:
            raise InvalidUsage("Request body is empty or not provided")

        # Save user object(s)
        talent_pool_candidate_ids = posted_data['talent_pool_candidates']

        # Talent_pool object(s) must be in a list
        if not isinstance(talent_pool_candidate_ids, list):
            raise InvalidUsage("Request body is not properly formatted")

        talent_pool = TalentPool.query.get(talent_pool_id)

        if not talent_pool:
            raise NotFoundError("Talent pool with id {} doesn't exist in database".format(talent_pool_id))

        if request.user.role.name != 'TALENT_ADMIN' and talent_pool.domain_id != request.user.domain_id:
            raise ForbiddenError("Talent pool and logged in user belong to different domains")

        talent_pool_group = TalentPoolGroup.query.filter_by(user_group_id=request.user.user_group_id,
                                                            talent_pool_id=talent_pool_id).first()
        if request.user.role.name == 'USER' and not talent_pool_group:
            raise ForbiddenError("User {} doesn't have appropriate permissions to "
                                 "remove candidates".format(request.user.id))

        for talent_pool_candidate_id in talent_pool_candidate_ids:
            if not is_number(talent_pool_candidate_id):
                raise InvalidUsage('Candidate id {} should be an integer'.format(talent_pool_candidate_id))
            else:
                talent_pool_candidate_id = int(talent_pool_candidate_id)

            talent_pool_candidate = TalentPoolCandidate.query.filter_by(candidate_id=talent_pool_candidate_id,
                                                                        talent_pool_id=talent_pool_id).first()
            if not talent_pool_candidate:
                raise NotFoundError("Candidate {} doesn't belong to talent-pool {}".format(
                        talent_pool_candidate_id, talent_pool_id))
            else:
                db.session.delete(talent_pool_candidate)

        db.session.commit()

        try:
            # Update Candidate Documents in Amazon Cloud Search
            headers = {'Authorization': request.oauth_token, 'Content-Type': 'application/json'}
            response = requests.post(CandidateApiUrl.CANDIDATES_DOCUMENTS_URI, headers=headers,
                                     data=json.dumps({'candidate_ids': talent_pool_candidate_ids}))

            if response.status_code != 204:
                raise Exception("Status Code: {} Response: {}".format(response.status_code, response.json()))

        except Exception as e:
            raise InvalidUsage("Couldn't update Candidate Documents in Amazon Cloud Search. Because: {}".format(e.message))

        return {'talent_pool_candidates': [int(talent_pool_candidate_id) for talent_pool_candidate_id in
                                           talent_pool_candidate_ids]}


class TalentPipelinesOfTalentPools(Resource):

    # Access token decorator
    decorators = [require_oauth()]

    # 'SELF' is for readability. It means this endpoint will be accessible to any user
    @require_all_permissions(Permission.PermissionNames.CAN_GET_TALENT_POOLS)
    def get(self, **kwargs):
        """
        GET /talent-pools/<id>/talent-pipelines  Fetch all talent-pipelines of a Talent-Pool

        :return A dictionary containing all talent-pipelines of a Talent Pool
        :rtype: dict
        """
        talent_pool_id = kwargs.get('id')
        talent_pool = TalentPool.query.get(talent_pool_id)

        if not talent_pool:
            raise NotFoundError("Talent pool with id {} doesn't exist in database".format(talent_pool_id))

        if request.user.role.name != 'TALENT_ADMIN' and talent_pool.domain_id != request.user.domain_id:
            raise ForbiddenError("Talent pool and logged in user belong to different domains")

        talent_pool_group = TalentPoolGroup.query.filter_by(user_group_id=request.user.user_group_id,
                                                            talent_pool_id=talent_pool_id).first()
        if request.user.role.name == 'USER' and not talent_pool_group:
            raise ForbiddenError("User {} doesn't have appropriate permissions to "
                                 "get talent-pipelines".format(request.user.id))

        page = request.args.get('page', DEFAULT_PAGE)
        per_page = request.args.get('per_page', DEFAULT_PAGE_SIZE)

        if not is_number(page) or not is_number(per_page) or int(page) < 1 or int(per_page) < 1:
            raise InvalidUsage("page and per_page should be positive integers")

        page = int(page)
        per_page = int(per_page)

        talent_pipelines_query = TalentPipeline.query.filter_by(talent_pool_id=talent_pool_id)
        talent_pipelines = talent_pipelines_query.paginate(page, per_page, False)
        talent_pipelines = talent_pipelines.items

        headers = generate_pagination_headers(talent_pipelines_query.count(), per_page, page)

        response = {
            'talent_pipelines': [talent_pipeline.to_dict(True, get_stats_generic_function)
                                 for talent_pipeline in talent_pipelines]
        }

        return ApiResponse(response=response, headers=headers, status=200)


@talent_pool_blueprint.route(CandidatePoolApi.TALENT_POOL_GET_STATS, methods=['GET'])
@require_oauth(allow_null_user=True)
def get_talent_pool_stats(talent_pool_id):
    """
    This method will return the statistics of a talent_pool over a given period of time with time-period = 1 day
    :param talent_pool_id: Id of a talent-pool
    :return: A list of time-series data
    """
    talent_pool = TalentPool.query.get(talent_pool_id)
    from_date_string = request.args.get('from_date', '')
    to_date_string = request.args.get('to_date', '')
    interval = request.args.get('interval', '1')
    offset = request.args.get('offset', 0)

    response = get_stats_generic_function(talent_pool, 'TalentPool', request.user, from_date_string,
                                          to_date_string, interval, False, offset)
    if 'is_update' in request.args:
        return '', 204
    else:
        return jsonify({'talent_pool_data': response})


@talent_pool_blueprint.route('statistics-update', methods=['GET'])
@require_oauth()
@require_all_permissions(Permission.PermissionNames.CAN_IMPERSONATE_USERS)
def update_all_statistics():
    
    container = request.args.get('talent-container', None)

    if container == 'talent-pipeline':
        update_talent_pipeline_stats.delay(True)
    elif container == 'talent_pool':
        update_talent_pool_stats.delay(True)
    elif container == 'smartlist':
        update_smartlist_stats.delay(True)
    elif container == 'all':
        update_talent_pipeline_stats.delay(True)
        update_talent_pool_stats.delay(True)
        update_smartlist_stats.delay(True)

    return '', 204


api = TalentApi(talent_pool_blueprint)
api.add_resource(TalentPoolApi, CandidatePoolApi.TALENT_POOL, CandidatePoolApi.TALENT_POOLS)
api.add_resource(TalentPoolGroupApi, CandidatePoolApi.TALENT_POOL_GROUPS)
api.add_resource(TalentPoolCandidateApi, CandidatePoolApi.TALENT_POOL_CANDIDATES)
api.add_resource(TalentPipelinesOfTalentPools, CandidatePoolApi.TALENT_PIPELINES_OF_TALENT_POOLS)

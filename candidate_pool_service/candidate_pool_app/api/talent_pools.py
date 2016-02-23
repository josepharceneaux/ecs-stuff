
__author__ = 'ufarooqi'

import json
import requests
from flask import request, Blueprint
from flask_restful import Resource
from datetime import datetime
from sqlalchemy import and_
from dateutil.parser import parse
from candidate_pool_service.common.error_handling import *
from candidate_pool_service.candidate_pool_app import logger
from candidate_pool_service.common.talent_api import TalentApi
from candidate_pool_service.common.routes import CandidateApiUrl
from candidate_pool_service.common.routes import CandidatePoolApi
from candidate_pool_service.common.utils.validators import is_number
from candidate_pool_service.common.models.talent_pools_pipelines import *
from candidate_pool_service.common.utils.auth_utils import require_oauth, require_any_role, require_all_roles
from candidate_pool_service.candidate_pool_app.talent_pools_pipelines_utilities import update_talent_pools_stats_task
from candidate_pool_service.common.models.user import DomainRole

talent_pool_blueprint = Blueprint('talent_pool_api', __name__)


class TalentPoolApi(Resource):

    # Access token decorator
    decorators = [require_oauth()]

    # 'SELF' is for readability. It means this endpoint will be accessible to any user
    @require_any_role('SELF', DomainRole.Roles.CAN_GET_TALENT_POOLS)
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
                raise NotFoundError(error_message="Talent pool with id %s doesn't exist in database" % talent_pool_id)

            if not request.user_can_edit_other_domains:
                if talent_pool.domain_id != request.user.domain_id:
                    raise ForbiddenError(error_message="User %s is not authorized to get talent-pool's info" %
                                                       request.user.id)

                talent_pool_group = TalentPoolGroup.query.filter_by(user_group_id=request.user.user_group_id,
                                                                    talent_pool_id=talent_pool_id).all()
                if not talent_pool_group and 'CAN_GET_TALENT_POOLS' not in request.valid_domain_roles:
                    raise ForbiddenError(error_message="User %s doesn't have appropriate permissions to get "
                                                       "talent-pools's info" % request.user.id)
            return {
                'talent_pool': {
                    'id': talent_pool.id,
                    'name': talent_pool.name,
                    'description': talent_pool.description,
                    'domain_id': talent_pool.domain_id,
                    'user_id': talent_pool.user_id
                }
            }
        # Getting all talent-pools of logged-in user's domain
        elif 'CAN_GET_TALENT_POOLS' in request.valid_domain_roles or request.user_can_edit_other_domains:
            talent_pools = TalentPool.query.filter_by(domain_id=request.user.domain_id).all()
            return {
                'talent_pools': [
                    {
                        'id': talent_pool.id,
                        'name': talent_pool.name,
                        'description': talent_pool.description,
                        'user_id': talent_pool.user_id,
                        'accessible_to_user_group_ids': [talent_pool_group.user_group_id for talent_pool_group in
                                                         TalentPoolGroup.query.filter_by(
                                                                 talent_pool_id=talent_pool.id
                                                         ).all()]
                    } for talent_pool in talent_pools
                ]
            }
        else:
            raise ForbiddenError("User %s is not authorized to get talent-pool's info" % request.user.id)

    @require_any_role(DomainRole.Roles.CAN_EDIT_TALENT_POOLS, DomainRole.Roles.CAN_EDIT_OTHER_DOMAIN_INFO)
    def put(self, **kwargs):
        """
        PUT /talent-pools/<id>      Modify an already existing talent-pool
        input: {'name': 'facebook-recruiting', 'description': ''}

        :return {'talent_pool': {'id': talent_pool_id}}
        :rtype: dict
        """

        talent_pool_id = kwargs.get('id')
        if not talent_pool_id:
            raise InvalidUsage(error_message="A valid talent_pool_id should be provided")

        talent_pool = TalentPool.query.get(talent_pool_id)
        if not talent_pool:
            raise NotFoundError(error_message="Talent pool with id %s doesn't exist in database" % talent_pool_id)

        posted_data = request.get_json(silent=True)
        if not posted_data or 'talent_pool' not in posted_data:
            raise InvalidUsage(error_message="Request body is empty or not provided")

        posted_data = posted_data['talent_pool']

        # posted_data must be in a dict
        if not isinstance(posted_data, dict):
            raise InvalidUsage(error_message="Request body is not properly formatted")

        if request.user.domain_id != talent_pool.domain_id and not request.user_can_edit_other_domains:
            raise ForbiddenError(error_message="User %s is not authorized to edit talent-pool's info" % request.user.id)

        name = posted_data.get('name')
        description = posted_data.get('description')

        if not name and not description:
            raise InvalidUsage(error_message="Neither modified name nor description is provided")

        if name and not TalentPool.query.filter_by(name=name, domain_id=talent_pool.domain_id).all():
            talent_pool.name = name
        elif name:
            raise InvalidUsage(error_message="Talent pool '%s' already exists in domain %s" % (name, talent_pool.domain_id))

        if description:
            talent_pool.description = description

        db.session.commit()

        return {
            'talent_pool': {'id': talent_pool.id}
        }

    @require_any_role(DomainRole.Roles.CAN_DELETE_TALENT_POOLS, DomainRole.Roles.CAN_EDIT_OTHER_DOMAIN_INFO)
    def delete(self, **kwargs):
        """
        DELETE /talent-pools/<id>      Delete an already existing talent-pool
        :return {'delete_talent_pool': {'id': talent_pool_id}}
        :rtype: dict
        """

        talent_pool_id = kwargs.get('id')
        if not talent_pool_id:
            raise InvalidUsage(error_message="A valid talent_pool_id should be provided")

        talent_pool = TalentPool.query.get(talent_pool_id)
        if not talent_pool:
            raise NotFoundError(error_message="Talent pool with id %s doesn't exist in database" % talent_pool_id)

        if request.user.domain_id != talent_pool.domain_id and not request.user_can_edit_other_domains:
            raise ForbiddenError(error_message="User %s is not authorized to delete a talent-pool" % request.user.id)

        talent_pool.delete()

        return {
            'talent_pool': {'id': talent_pool.id}
        }

    @require_any_role(DomainRole.Roles.CAN_ADD_TALENT_POOLS, DomainRole.Roles.CAN_EDIT_OTHER_DOMAIN_INFO)
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
            raise InvalidUsage(error_message="Request body is empty or not provided")

        # Save user object(s)
        talent_pools = posted_data['talent_pools']

        # Talent_pool object(s) must be in a list
        if not isinstance(talent_pools, list):
            raise InvalidUsage(error_message="Request body is not properly formatted")

        talent_pool_objects = []
        for talent_pool in talent_pools:

            name = talent_pool.get('name', '').strip()
            description = talent_pool.get('description', '').strip()
            if request.user_can_edit_other_domains:
                request.user = User.query.get(talent_pool.get('user_id', request.user.id))
                if not request.user:
                    raise InvalidUsage("User with id %s doesn't exist in Database" % request.user.id)

            if not name:
                raise InvalidUsage(error_message="A valid name should be provided to create a talent-pool")

            if name and TalentPool.query.filter_by(name=name, domain_id=request.user.domain_id).all():
                raise InvalidUsage(error_message="Talent pool '%s' already exists in domain %s" % (name, request.user.domain_id))

            # Add TalentPool
            talent_pool_object = TalentPool(name=name, description=description, domain_id=request.user.domain_id,
                                            user_id=request.user.id)
            talent_pool_objects.append(talent_pool_object)
            db.session.add(talent_pool_object)
            db.session.flush()

            # Add TalentPoolGroup to associate new TalentPool with existing UserGroup
            db.session.add(TalentPoolGroup(talent_pool_id=talent_pool_object.id,
                                           user_group_id=request.user.user_group_id))

        db.session.commit()
        return {'talent_pools': [talent_pool_object.id for talent_pool_object in talent_pool_objects]}


class TalentPoolGroupApi(Resource):

    # Access token decorator
    decorators = [require_oauth()]

    # 'SELF' is for readability. It means this endpoint will be accessible to any user
    @require_any_role('SELF', DomainRole.Roles.CAN_GET_TALENT_POOLS_OF_GROUP)
    def get(self, **kwargs):
        """
        GET /groups/<group_id>/talent_pools     Fetch all talent-pool objects of given user group

        :return A dictionary containing all talent-pools of a user group
        :rtype: dict
        """

        user_group_id = kwargs.get('group_id')
        user_group = UserGroup.query.get(user_group_id)

        if not user_group:
            raise NotFoundError(error_message="User group with id %s doesn't exist" % user_group_id)
        if not request.user_can_edit_other_domains:
            if user_group.domain_id != request.user.domain_id:
                raise ForbiddenError(error_message="Logged-in user belongs to different domain as given user group")

            if user_group.id != request.user.user_group_id and 'CAN_GET_TALENT_POOLS_OF_GROUP' not in \
                    request.valid_domain_roles:
                raise ForbiddenError(error_message="Either logged-in user belongs to different group as "
                                                   "input user group or it doesn't have appropriate roles")

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

    @require_any_role(DomainRole.Roles.CAN_DELETE_TALENT_POOLS_FROM_GROUP, DomainRole.Roles.CAN_EDIT_OTHER_DOMAIN_INFO)
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
            raise InvalidUsage(error_message="Request body is empty or not provided")

        # Save user object(s)
        talent_pool_ids = posted_data['talent_pools']

        # Talent_pool object(s) must be in a list
        if not isinstance(talent_pool_ids, list):
            raise InvalidUsage(error_message="Request body is not properly formatted")

        user_group = UserGroup.query.get(user_group_id)

        if not user_group:
            raise NotFoundError(error_message="User group with id %s doesn't exist" % user_group_id)

        if request.user.domain_id != user_group.domain_id and not request.user_can_edit_other_domains:
            raise ForbiddenError(error_message="Logged-in user and given user-group belong to different domains")

        for talent_pool_id in talent_pool_ids:

            if not is_number(talent_pool_id):
                raise InvalidUsage('Talent pool id %s should be an integer' % talent_pool_id)
            else:
                talent_pool_id = int(talent_pool_id)

            talent_pool_group = TalentPoolGroup.query.filter_by(user_group_id=user_group_id,
                                                                talent_pool_id=talent_pool_id).first()
            if not talent_pool_group:
                raise NotFoundError(error_message="Talent pool %s doesn't belong to group %s" % (talent_pool_id,
                                                                                                 user_group_id))
            else:
                db.session.delete(talent_pool_group)

        db.session.commit()

        return {'talent_pools': [int(talent_pool_id) for talent_pool_id in talent_pool_ids]}

    @require_any_role(DomainRole.Roles.CAN_ADD_TALENT_POOLS_TO_GROUP, DomainRole.Roles.CAN_EDIT_OTHER_DOMAIN_INFO)
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
            raise InvalidUsage(error_message="Request body is empty or not provided")

        # Save user object(s)
        talent_pool_ids = posted_data['talent_pools']

        # Talent_pool object(s) must be in a list
        if not isinstance(talent_pool_ids, list):
            raise InvalidUsage(error_message="Request body is not properly formatted")

        user_group = UserGroup.query.get(user_group_id)

        if not user_group:
            raise NotFoundError(error_message="User group with id %s doesn't exist" % user_group_id)

        if request.user.domain_id != user_group.domain_id and not request.user_can_edit_other_domains:
            raise ForbiddenError(error_message="Logged-in user and given user-group belong to different domains")

        for talent_pool_id in talent_pool_ids:

            if not is_number(talent_pool_id):
                raise InvalidUsage('Talent pool id %s should be an integer' % talent_pool_id)
            else:
                talent_pool_id = int(talent_pool_id)

            if TalentPoolGroup.query.filter_by(user_group_id=user_group_id, talent_pool_id=talent_pool_id).first():
                raise InvalidUsage(error_message="Talent pool %s already belongs to user group %s" % (
                    talent_pool_id, user_group_id))

            talent_pool = TalentPool.query.get(talent_pool_id)
            if not talent_pool:
                raise NotFoundError(error_message="Talent pool %s doesn't exist in database" % talent_pool_id)

            if user_group.domain_id != talent_pool.domain_id:
                raise InvalidUsage(error_message="Talent pool %s and user_group %s belong to different domain" % (
                    talent_pool.name, user_group.name))

            db.session.add(TalentPoolGroup(talent_pool_id=talent_pool_id, user_group_id=user_group_id))

        db.session.commit()
        return {'added_talent_pools': [int(talent_pool_id) for talent_pool_id in talent_pool_ids]}


class TalentPoolCandidateApi(Resource):

    # Access token decorator
    decorators = [require_oauth()]

    # 'SELF' is for readability. It means this endpoint will be accessible to any user
    @require_any_role('SELF', DomainRole.Roles.CAN_GET_CANDIDATES_FROM_TALENT_POOL)
    def get(self, **kwargs):
        """
        GET /talent-pools/<id>/candidates  Fetch Candidate Statistics of Talent-Pool

        :return A dictionary containing Candidate Statistics of a Talent Pool
        :rtype: dict
        """
        talent_pool_id = kwargs.get('id')
        talent_pool = TalentPool.query.get(talent_pool_id)

        if not talent_pool:
            raise NotFoundError(error_message="Talent pool with id %s doesn't exist in database" % talent_pool_id)

        if talent_pool.domain_id != request.user.domain_id:
            raise ForbiddenError(error_message="Talent pool and logged in user belong to different domains")

        if not TalentPoolGroup.query.filter_by(user_group_id=request.user.user_group_id, talent_pool_id=talent_pool_id)\
                .all() and 'CAN_GET_CANDIDATES_FROM_TALENT_POOL' not in request.valid_domain_roles:
            raise ForbiddenError(error_message="User %s doesn't have appropriate permissions to get candidates"
                                                  % request.user.id)

        total_candidate = TalentPoolCandidate.query.filter_by(talent_pool_id=talent_pool_id).all()

        return {
            'talent_pool_candidates':
                {
                    'name': talent_pool.name,
                    'total_found': len(total_candidate)
                }
        }

    # 'SELF' is for readability. It means this endpoint will be accessible to any user
    @require_any_role('SELF', DomainRole.Roles.CAN_ADD_CANDIDATES_TO_TALENT_POOL)
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
            raise InvalidUsage(error_message="Request body is empty or not provided")

        # Save user object(s)
        talent_pool_candidate_ids = posted_data['talent_pool_candidates']

        # Talent_pool object(s) must be in a list
        if not isinstance(talent_pool_candidate_ids, list):
            raise InvalidUsage(error_message="Request body is not properly formatted")

        talent_pool = TalentPool.query.get(talent_pool_id)

        if not talent_pool:
            raise NotFoundError(error_message="Talent pool with id %s doesn't exist in database" % talent_pool_id)

        if talent_pool.domain_id != request.user.domain_id:
            raise ForbiddenError(error_message="Talent pool and logged in user belong to different domains")

        if not TalentPoolGroup.query.filter_by(user_group_id=request.user.user_group_id, talent_pool_id=talent_pool_id)\
                .all() and 'CAN_ADD_CANDIDATES_TO_TALENT_POOL' not in request.valid_domain_roles:
            raise ForbiddenError(error_message="User %s doesn't have appropriate permissions to add candidates"
                                                  % request.user.id)

        try:
            talent_pool_candidate_ids = [int(talent_pool_candidate_id) for talent_pool_candidate_id in
                                         talent_pool_candidate_ids]
        except:
            raise InvalidUsage(error_message="All candidate ids should be integer")

        # Candidates which already exist in a given talent-pool
        already_existing_candidates_in_talent_pool = TalentPoolCandidate.query.filter(and_(
            TalentPoolCandidate.talent_pool_id == talent_pool_id, TalentPoolCandidate.candidate_id.in_(
                talent_pool_candidate_ids))).all()

        # No candidate should already exist in a given talent-pool
        if len(already_existing_candidates_in_talent_pool) > 0:
            raise InvalidUsage(error_message="Candidate %s already exists in talent-pool %s" % (
                already_existing_candidates_in_talent_pool[0].id, talent_pool_id))

        # Candidates with input candidate ids exist in database or not
        for talent_pool_candidate_id in talent_pool_candidate_ids:
            talent_pool_candidate = Candidate.query.get(talent_pool_candidate_id)
            if not talent_pool_candidate:
                raise NotFoundError(error_message="Candidate with id %s doesn't exist in database" % talent_pool_candidate_id)

            if talent_pool_candidate.user.domain_id != talent_pool.domain_id:
                raise ForbiddenError("Talent Pool %s and Candidate %s belong to different domain" %
                                     (talent_pool.id, talent_pool_candidate.id))
            db.session.add(TalentPoolCandidate(talent_pool_id=talent_pool_id, candidate_id=talent_pool_candidate_id))

        db.session.commit()

        try:
            # Update Candidate Documents in Amazon Cloud Search
            headers = {'Authorization': request.oauth_token, 'Content-Type': 'application/json'}
            response = requests.post(CandidateApiUrl.CANDIDATES_DOCUMENTS_URI, headers=headers,
                                     data=json.dumps({'candidate_ids': talent_pool_candidate_ids}))

            if response.status_code != 204:
                raise Exception("Status Code: %s Response: %s" % (response.status_code, response.json()))

        except Exception as e:
            raise InvalidUsage(error_message="Couldn't update Candidate Documents in Amazon Cloud Search. "
                                             "Because: %s" % e.message)

        return {'added_talent_pool_candidates': [int(talent_pool_candidate_id) for talent_pool_candidate_id in
                                                 talent_pool_candidate_ids]}

    # 'SELF' is for readability. It means this endpoint will be accessible to any user
    @require_any_role('SELF', DomainRole.Roles.CAN_DELETE_CANDIDATES_FROM_TALENT_POOL)
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
            raise InvalidUsage(error_message="Request body is empty or not provided")

        # Save user object(s)
        talent_pool_candidate_ids = posted_data['talent_pool_candidates']

        # Talent_pool object(s) must be in a list
        if not isinstance(talent_pool_candidate_ids, list):
            raise InvalidUsage(error_message="Request body is not properly formatted")

        talent_pool = TalentPool.query.get(talent_pool_id)

        if not talent_pool:
            raise NotFoundError(error_message="Talent pool with id %s doesn't exist in database" % talent_pool_id)

        if talent_pool.domain_id != request.user.domain_id:
            raise ForbiddenError(error_message="Talent pool and logged in user belong to different domains")

        if not TalentPoolGroup.query.filter_by(user_group_id=request.user.user_group_id, talent_pool_id=talent_pool_id)\
                .all() and 'CAN_DELETE_CANDIDATES_FROM_TALENT_POOL' not in request.valid_domain_roles:
            raise ForbiddenError(error_message="User %s doesn't have appropriate permissions to remove candidates"
                                                  % request.user.id)

        for talent_pool_candidate_id in talent_pool_candidate_ids:
            if not is_number(talent_pool_candidate_id):
                raise InvalidUsage('Candidate id %s should be an integer' % talent_pool_candidate_id)
            else:
                talent_pool_candidate_id = int(talent_pool_candidate_id)

            talent_pool_candidate = TalentPoolCandidate.query.filter_by(candidate_id=talent_pool_candidate_id,
                                                                        talent_pool_id=talent_pool_id).first()
            if not talent_pool_candidate:
                raise NotFoundError(error_message="Candidate %s doesn't belong to talent-pool %s" % (
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
                raise Exception(error_message="Status Code: %s Response: %s" % (response.status_code, response.json()))

        except Exception as e:
            raise InvalidUsage(error_message="Couldn't update Candidate Documents in Amazon Cloud Search. "
                                             "Because: %s" % e.message)

        return {'talent_pool_candidates': [int(talent_pool_candidate_id) for talent_pool_candidate_id in
                                           talent_pool_candidate_ids]}


@talent_pool_blueprint.route(CandidatePoolApi.TALENT_POOL_UPDATE_STATS, methods=['POST'])
@require_oauth(allow_null_user=True)
def update_talent_pools_stats():
    """
    This method will update the statistics of all talent-pools daily.
    :return: None
    """
    logger.info("TalentPool statistics update process has been started")
    update_talent_pools_stats_task.delay()
    return '', 204


@talent_pool_blueprint.route(CandidatePoolApi.TALENT_POOL_GET_STATS, methods=['GET'])
@require_oauth()
def get_talent_pool_stats(talent_pool_id):
    """
    This method will return the statistics of a talent_pool over a given period of time with time-period = 1 day
    :param talent_pool_id: Id of a talent-pool
    :return: A list of time-series data
    """
    talent_pool = TalentPool.query.get(talent_pool_id)
    if not talent_pool:
        raise NotFoundError(error_message="TalentPool with id=%s doesn't exist in database" % talent_pool_id)

    if talent_pool.user.domain_id != request.user.domain_id:
        raise ForbiddenError(error_message="Logged-in user %s is unauthorized to get stats of talent-pool %s"
                                           % (request.user.id, talent_pool.id))

    from_date_string = request.args.get('from_date', '')
    to_date_string = request.args.get('to_date', '')
    interval = request.args.get('interval', '1')

    try:
        from_date = parse(from_date_string) if from_date_string else datetime.fromtimestamp(0)
        to_date = parse(to_date_string) if to_date_string else datetime.utcnow()
    except Exception as e:
        raise InvalidUsage(error_message="Either 'from_date' or 'to_date' is invalid because: %s" % e.message)

    if not is_number(interval):
        raise InvalidUsage("Interval '%s' should be integer" % interval)

    interval = int(interval)
    if interval < 1:
        raise InvalidUsage("Interval's value should be greater than or equal to 1 day")

    talent_pool_stats = TalentPoolStats.query.filter(and_(TalentPoolStats.talent_pool_id == talent_pool_id,
                                                          TalentPoolStats.added_datetime >= from_date,
                                                          TalentPoolStats.added_datetime <= to_date)).all()
    talent_pool_stats.reverse()
    talent_pool_stats = talent_pool_stats[::interval]

    # Computing number_of_candidates_added by subtracting candidate count of previous day from candidate
    # count of current_day
    talent_pool_stats = map(lambda (i, talent_pool_stat): {
        'total_number_of_candidates': talent_pool_stat.total_number_of_candidates,
        'number_of_candidates_added': (talent_pool_stat.total_number_of_candidates - (
            talent_pool_stats[i + 1].total_number_of_candidates if i + 1 < len(talent_pool_stats)
            else talent_pool_stat.total_number_of_candidates)),
        'added_datetime': talent_pool_stat.added_datetime.isoformat(),
        'candidates_engagement': talent_pool_stat.candidates_engagement
    }, enumerate(talent_pool_stats))

    return jsonify({'talent_pool_data': talent_pool_stats})


@talent_pool_blueprint.route(CandidatePoolApi.TALENT_PIPELINES_IN_TALENT_POOL_GET_STATS, methods=['GET'])
@require_oauth()
def get_talent_pipelines_in_talent_pool_stats(talent_pool_id):
    """
    This method will return the statistics of all talent-pipelines in a talent_pool over a given period of time
    with time-period = 1 day
    :param talent_pool_id: Id of a talent-pool
    :return: A list of time-series data
    """
    talent_pool = TalentPool.query.get(talent_pool_id)
    if not talent_pool:
        raise NotFoundError(error_message="TalentPool with id=%s doesn't exist in database" % talent_pool_id)

    if talent_pool.user.domain_id != request.user.domain_id:
        raise ForbiddenError(error_message="Logged-in user %s is unauthorized to get stats of talent-pool %s"
                                           % (request.user.id, talent_pool.id))

    from_date_string = request.args.get('from_date', '')
    to_date_string = request.args.get('to_date', '')
    interval = request.args.get('interval', '1')

    try:
        from_date = parse(from_date_string) if from_date_string else datetime.fromtimestamp(0)
        to_date = parse(to_date_string) if to_date_string else datetime.utcnow()
    except Exception as e:
        raise InvalidUsage(error_message="Either 'from_date' or 'to_date' is invalid because: %s" % e.message)

    if not is_number(interval):
        raise InvalidUsage("Interval '%s' should be integer" % interval)

    interval = int(interval)
    if interval < 1:
        raise InvalidUsage("Interval's value should be greater than or equal to 1 day")

    talent_pipelines_in_talent_pool_stats = TalentPipelinesInTalentPoolStats.query.filter(and_(
            TalentPipelinesInTalentPoolStats.talent_pool_id == talent_pool_id,
            TalentPipelinesInTalentPoolStats.added_datetime >= from_date,
            TalentPipelinesInTalentPoolStats.added_datetime <= to_date)).all()

    talent_pipelines_in_talent_pool_stats.reverse()

    talent_pipelines_in_talent_pool_stats = talent_pipelines_in_talent_pool_stats[::interval]

    # Computing average_number_of_candidates_added by subtracting candidate count of previous day from candidate
    # count of current_day
    talent_pipelines_in_talent_pool_stats = map(lambda (i, stat_row): {
        'average_number_of_candidates': stat_row.average_number_of_candidates,
        'average_number_of_candidates_added': (stat_row.average_number_of_candidates - (
            talent_pipelines_in_talent_pool_stats[i + 1].average_number_of_candidates
            if i + 1 < len(talent_pipelines_in_talent_pool_stats) else stat_row.average_number_of_candidates)),
        'added_datetime': stat_row.added_datetime.isoformat()
    }, enumerate(talent_pipelines_in_talent_pool_stats))

    return jsonify({'talent_pool_data': talent_pipelines_in_talent_pool_stats})

api = TalentApi(talent_pool_blueprint)
api.add_resource(TalentPoolApi, CandidatePoolApi.TALENT_POOL, CandidatePoolApi.TALENT_POOLS)
api.add_resource(TalentPoolGroupApi, CandidatePoolApi.TALENT_POOL_GROUPS)
api.add_resource(TalentPoolCandidateApi, CandidatePoolApi.TALENT_POOL_CANDIDATES)

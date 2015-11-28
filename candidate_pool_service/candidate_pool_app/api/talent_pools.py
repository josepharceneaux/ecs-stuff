__author__ = 'ufarooqi'

from flask import request
from flask_restful import Resource
from sqlalchemy import and_
from candidate_pool_service.common.utils.validators import is_number
from candidate_pool_service.common.models.talent_pools_pipelines import *
from candidate_pool_service.common.utils.auth_utils import require_oauth, require_any_role, require_all_roles
from candidate_pool_service.common.error_handling import *


class TalentPoolApi(Resource):

    # Access token decorator
    decorators = [require_oauth]

    @require_any_role('SELF', 'CAN_GET_TALENT_POOLS')
    def get(self, **kwargs):
        """
        GET /talent-pools/<id>          Fetch talent-pool object
        GET /talent-pools               Fetch all talent-pool objects of domain of logged-in user

        :return A dictionary containing talent-pool basic info or a dictionary containing all talent-pools of a domain
        :rtype: dict
        """

        talent_pool_id = kwargs.get('id')

        if talent_pool_id:
            talent_pool = TalentPool.query.get(talent_pool_id)

            if not talent_pool:
                raise NotFoundError(error_message="Talent pool with id %s doesn't exist in database" % talent_pool_id)

            if talent_pool.domain_id != request.user.domain_id:
                raise UnauthorizedError(error_message="User %s is not authorized to get talent-pool's info" %
                                                      request.user.id)

            if not TalentPoolGroup.query.filter_by(user_group_id=request.user.user_group_id,
                                                   talent_pool_id=talent_pool_id).all() and 'CAN_GET_TALENT_POOLS' \
                    not in request.valid_domain_roles:
                raise UnauthorizedError(error_message="User %s doesn't have appropriate permissions to get "
                                                      "talent-pools's info" % request.user.id)
            return {
                'talent_pool': {
                    'id': talent_pool.id,
                    'name': talent_pool.name,
                    'description': talent_pool.description,
                    'domain_id': talent_pool.domain_id,
                    'user_id': talent_pool.owner_user_id
                }
            }
        elif 'CAN_GET_TALENT_POOLS' in request.valid_domain_roles:
            talent_pools = TalentPool.query.filter_by(domain_id=request.user.domain_id).all()
            return {
                'talent_pools': [
                    {
                        'id': talent_pool.id,
                        'name': talent_pool.name,
                        'description': talent_pool.description,
                        'domain_id': talent_pool.domain_id,
                        'user_id': talent_pool.owner_user_id

                    } for talent_pool in talent_pools
                ]
            }
        else:
            raise UnauthorizedError("User %s is not authorized to get talent-pool's info" % request.user.id)

    @require_all_roles('CAN_EDIT_TALENT_POOLS')
    def put(self, **kwargs):
        """
        PUT /talent-pools/<id>      Modify an already existing talent-pool
        input: {'name': 'facebook-recruiting', 'description': ''}

        :return {'updated_talent_pool': {'id': talent_pool_id}}
        :rtype: dict
        """

        talent_pool_id = kwargs.get('id')
        if not talent_pool_id:
            raise InvalidUsage(error_message="A valid talent_pool_id should be provided")

        talent_pool = TalentPool.query.get(talent_pool_id)
        if not talent_pool:
            raise NotFoundError(error_message="Talent pool with id %s doesn't exist in database" % talent_pool_id)

        posted_data = request.get_json(silent=True)
        if not posted_data:
            raise InvalidUsage(error_message="Request body is empty or not provided")

        if request.user.domain_id != talent_pool.domain_id:
            raise UnauthorizedError(error_message="User %s is not authorized to edit talent-pool's info" % request.user.id)

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
            'updated_talent_pool': {'id': talent_pool.id}
        }

    @require_all_roles('CAN_DELETE_TALENT_POOLS')
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

        if request.user.domain_id != talent_pool.domain_id:
            raise UnauthorizedError(error_message="User %s is not authorized to delete a talent-pool" % request.user.id)

        talent_pool.delete()

        return {
            'deleted_talent_pool': {'id': talent_pool.id}
        }

    @require_all_roles('CAN_ADD_TALENT_POOLS')
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

            if not name:
                raise InvalidUsage(error_message="A valid should be provided to create a talent-pool")

            if name and TalentPool.query.filter_by(name=name, domain_id=request.user.domain_id).all():
                raise InvalidUsage(error_message="Talent pool '%s' already exists in domain %s" % (name, request.user.domain_id))

            talent_pool_object = TalentPool(name=name, description=description, domain_id=request.user.domain_id,
                                            owner_user_id=request.user.id)
            talent_pool_objects.append(talent_pool_object)
            db.session.add(talent_pool_object)

        db.session.commit()
        return {'talent_pools': [talent_pool_object.id for talent_pool_object in talent_pool_objects]}


class TalentPoolGroupApi(Resource):

    # Access token decorator
    decorators = [require_oauth]

    @require_any_role('SELF', 'CAN_GET_TALENT_POOLS_OF_GROUP')
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

        if user_group.domain_id != request.user.domain_id:
            raise UnauthorizedError(error_message="Logged-in user belongs to different domain as given user group")

        if user_group.id != request.user.user_group_id and 'CAN_GET_TALENT_POOLS_OF_GROUP' not in request.valid_domain_roles:
            raise UnauthorizedError(error_message="Either logged-in user belongs to different group as input user group"
                                                  "or it doesn't have appropriate roles")

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
                    'owner_user_id': talent_pool.owner_user_id

                } for talent_pool in talent_pools
            ]
        }

    @require_all_roles('CAN_DELETE_TALENT_POOLS_FROM_GROUP')
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

        if request.user.domain_id != user_group.domain_id:
            raise UnauthorizedError(error_message="Logged-in user and given user-group belong to different domains")

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

        return {'deleted_talent_pools': [int(talent_pool_id) for talent_pool_id in talent_pool_ids]}

    @require_all_roles('CAN_ADD_TALENT_POOLS_TO_GROUP')
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

        if request.user.domain_id != user_group.domain_id:
            raise UnauthorizedError(error_message="Logged-in user and given user-group belong to different domains")

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
    decorators = [require_oauth]

    @require_any_role('SELF', 'CAN_GET_CANDIDATES_FROM_TALENT_POOL')
    def get(self, **kwargs):
        """
        GET /talent-pools/<id>/candidates     Fetch all candidates of a talent-pol

        :return A dictionary containing information of all candidates of a talent-pool
        :rtype: dict
        """
        talent_pool_id = kwargs.get('id')
        talent_pool = TalentPool.query.get(talent_pool_id)

        if not talent_pool:
            raise NotFoundError(error_message="Talent pool with id %s doesn't exist in database" % talent_pool_id)

        if talent_pool.domain_id != request.user.domain_id:
            raise UnauthorizedError(error_message="Talent pool and logged in user belong to different domains")

        if not TalentPoolGroup.query.filter_by(user_group_id=request.user.user_group_id, talent_pool_id=talent_pool_id)\
                .all() and 'CAN_GET_CANDIDATES_FROM_TALENT_POOL' not in request.valid_domain_roles:
            raise UnauthorizedError(error_message="User %s doesn't have appropriate permissions to get candidates"
                                                  % request.user.id)

        candidate_ids = [talent_pool_candidate.candidate_id for talent_pool_candidate in
                         TalentPoolCandidate.query.filter_by(talent_pool_id=talent_pool_id)]
        talent_pool_candidates = Candidate.query.filter(Candidate.id.in_(candidate_ids)).all()
        return {
            'talent_pool_candidates': [
                {
                    'id': talent_pool_candidate.id,
                    'name': talent_pool_candidate.last_name + ', ' + talent_pool_candidate.first_name,

                } for talent_pool_candidate in talent_pool_candidates
            ]
        }

    @require_any_role('SELF', 'CAN_ADD_CANDIDATES_TO_TALENT_POOL')
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
            raise UnauthorizedError(error_message="Talent pool and logged in user belong to different domains")

        if not TalentPoolGroup.query.filter_by(user_group_id=request.user.user_group_id, talent_pool_id=talent_pool_id)\
                .all() and 'CAN_ADD_CANDIDATES_TO_TALENT_POOL' not in request.valid_domain_roles:
            raise UnauthorizedError(error_message="User %s doesn't have appropriate permissions to add candidates"
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
            if not Candidate.query.get(talent_pool_candidate_id):
                raise NotFoundError(error_message="Candidate with id %s doesn't exist in database" % talent_pool_candidate_id)

            db.session.add(TalentPoolCandidate(talent_pool_id=talent_pool_id, candidate_id=talent_pool_candidate_id))

        db.session.commit()
        return {'added_talent_pool_candidates': [int(talent_pool_candidate_id) for talent_pool_candidate_id in
                                                 talent_pool_candidate_ids]}

    @require_any_role('SELF', 'CAN_DELETE_CANDIDATES_FROM_TALENT_POOL')
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
            raise UnauthorizedError(error_message="Talent pool and logged in user belong to different domains")

        if not TalentPoolGroup.query.filter_by(user_group_id=request.user.user_group_id, talent_pool_id=talent_pool_id)\
                .all() and 'CAN_DELETE_CANDIDATES_FROM_TALENT_POOL' not in request.valid_domain_roles:
            raise UnauthorizedError(error_message="User %s doesn't have appropriate permissions to remove candidates"
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

        return {'deleted_talent_pool_candidates': [int(talent_pool_candidate_id) for talent_pool_candidate_id in
                                                   talent_pool_candidate_ids]}

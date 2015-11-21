__author__ = 'ufarooqi'

from flask import request
from flask_restful import Resource
from sqlalchemy import and_
from candidate_pool_service.common.utils.validators import is_number
from candidate_pool_service.common.models.talent_pools_pipelines import *
from candidate_pool_service.common.utils.auth_utils import require_oauth, require_any_role
from candidate_pool_service.common.error_handling import *
from candidate_pool_utilities import is_user_authenticated_to_access_talent_pool


class TalentPoolApi(Resource):

    # Access token and role authentication decorators
    decorators = [require_oauth]

    @require_any_role()
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
            elif is_user_authenticated_to_access_talent_pool(talent_pool=talent_pool):
                return {
                    'talent_pool': {
                        'id': talent_pool.id,
                        'name': talent_pool.name,
                        'description': talent_pool.description,
                        'domain_id': talent_pool.domain_id,
                        'user_id': talent_pool.owner_user_id
                    }
                }
        elif is_user_authenticated_to_access_talent_pool():
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
        raise UnauthorizedError(error_message="Either logged-in user is not admin or it doesn't belong to same domain "
                                              "as talent-pool")

    @require_any_role('ADMIN', 'DOMAIN_ADMIN', 'CAN_MANAGE_TALENT_POOLS')
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

        if not request.is_admin_user and request.user.domain_id != talent_pool.domain_id:
            raise UnauthorizedError(error_message="Either logged-in user should be admin or belong to same domain as "
                                                  "talent-pool")

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

    @require_any_role('ADMIN', 'DOMAIN_ADMIN', 'CAN_MANAGE_TALENT_POOLS')
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

        if not request.is_admin_user and request.user.domain_id != talent_pool.domain_id:
            raise UnauthorizedError(error_message="Either logged-in user should be admin or belong to same domain as "
                                                  "talent-pool")
        talent_pool.delete()

        return {
            'deleted_talent_pool': {'id': talent_pool.id}
        }

    @require_any_role('ADMIN', 'DOMAIN_ADMIN', 'CAN_MANAGE_TALENT_POOLS')
    def post(self, **kwargs):
        """
        POST /talent-pools    Create new empty talent pools
        input: {'talent_pools': [talent_pool_dict1, talent_pool_dict2, talent_pool_dict3, ... ]}

        Take a JSON dictionary containing array of TalentPool dictionaries
        A single talent-pool dict must contain pool's name and domain id
        If domain_id is not provided then domain_id of logged-in user would be used

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
            domain_id = talent_pool.get('domain_id', request.user.domain_id)

            if not is_number(domain_id):
                raise InvalidUsage('Domain_id %s should be an integer' % domain_id)
            else:
                domain_id = int(domain_id)

            if not Domain.query.get(domain_id):
                raise NotFoundError(error_message="Domain with id %s doesn't exist in Database")

            if not request.is_admin_user and request.user.domain_id != domain_id:
                raise UnauthorizedError('You are not authorized to add a talent-pool in domain %s' % domain_id)

            if not name:
                raise InvalidUsage(error_message="A valid should be provided to create a talent-pool")

            if name and TalentPool.query.filter_by(name=name, domain_id=domain_id).all():
                raise InvalidUsage(error_message="Talent pool '%s' already exists in domain %s" % (name, domain_id))

            talent_pool_object = TalentPool(name=name, description=description, domain_id=domain_id,
                                            owner_user_id=request.user.id)
            talent_pool_objects.append(talent_pool_object)
            db.session.add(talent_pool_object)

        db.session.commit()
        return {'talent_pools': [talent_pool_object.id for talent_pool_object in talent_pool_objects]}


class TalentPoolGroupApi(Resource):

    # Access token and role authentication decorators
    decorators = [require_oauth]

    @require_any_role()
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
        elif user_group.id == request.user.user_group_id or is_user_authenticated_to_access_talent_pool(user_group=user_group):
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
        else:
            raise UnauthorizedError(error_message="Either logged-in user is not admin or it doesn't belong to same "
                                                  "domain as user group")

    @require_any_role('ADMIN', 'DOMAIN_ADMIN', 'CAN_MANAGE_TALENT_POOLS', 'GROUP_ADMIN')
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
        elif is_user_authenticated_to_access_talent_pool(user_group=user_group):

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
        else:
            raise UnauthorizedError(error_message="Either logged-in user is not admin or it doesn't belong to same "
                                                  "domain as user group")

    @require_any_role('ADMIN', 'DOMAIN_ADMIN', 'CAN_MANAGE_TALENT_POOLS', 'GROUP_ADMIN')
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
        elif is_user_authenticated_to_access_talent_pool(user_group=user_group):

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

        else:
            raise UnauthorizedError(error_message="Either logged-in user is not admin or it doesn't belong to same "
                                                  "domain as user group")


class TalentPoolCandidateApi(Resource):

    # Access token and role authentication decorators
    decorators = [require_any_role(), require_oauth]

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
        elif is_user_authenticated_to_access_talent_pool(talent_pool=talent_pool):
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
        else:
            raise UnauthorizedError(error_message="Either logged-in user is not admin or it doesn't belong to same "
                                                  "domain as user group")

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
        elif is_user_authenticated_to_access_talent_pool(talent_pool=talent_pool):
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

        else:
            raise UnauthorizedError(error_message="Either logged-in user is not admin or it doesn't belong to same "
                                                  "domain as user group")

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
        elif is_user_authenticated_to_access_talent_pool(talent_pool=talent_pool):

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
        else:
            raise UnauthorizedError(error_message="Either logged-in user is not admin or it doesn't belong to same "
                                                  "domain as user group")

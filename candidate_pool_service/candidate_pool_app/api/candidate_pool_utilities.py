__author__ = 'ufarooqi'

from flask import request
from candidate_pool_service.common.models.talent_pools_pipelines import TalentPoolGroup


def is_user_authenticated_to_access_talent_pool(talent_pool=None, user_group=None):
    """
    Check either a user possess given roles or belong to a given group
    :param TalentPool talent_pool: Talent-pool object
    :return: True or False based on user roles and groups
    :rtype: bool
    """

    if talent_pool:
        is_user_and_talent_pool_belongs_to_same_group = TalentPoolGroup.query.filter_by(
            user_group_id=request.user.user_group_id, talent_pool_id=talent_pool.id).first()
        return request.is_admin_user or (('DOMAIN_ADMIN' in request.valid_domain_roles or 'CAN_MANAGE_TALENT_POOLS' in
                                          request.valid_domain_roles) and request.user.domain_id ==
                                         talent_pool.domain_id) or is_user_and_talent_pool_belongs_to_same_group
    elif user_group:
        return request.is_admin_user or (('DOMAIN_ADMIN' in request.valid_domain_roles or 'CAN_MANAGE_TALENT_POOLS' in
                                          request.valid_domain_roles) and request.user.domain_id ==
                                         user_group.domain_id) or ('GROUP_ADMIN' in request.valid_domain_roles and
                                                                   request.user.user_group_id == user_group.id)
    else:
        return request.is_admin_user or 'DOMAIN_ADMIN' in request.valid_domain_roles or 'CAN_MANAGE_TALENT_POOLS' in \
                                                                                        request.valid_domain_roles


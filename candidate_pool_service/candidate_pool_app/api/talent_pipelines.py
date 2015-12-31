__author__ = 'ufarooqi'

import datetime
import json
from flask import request, Blueprint
from dateutil import parser
from sqlalchemy import and_
from dateutil.parser import parse
from flask_restful import Resource
from candidate_pool_service.common.error_handling import *
from candidate_pool_service.common.talent_api import TalentApi
from candidate_pool_service.common.utils.validators import is_number
from candidate_pool_service.common.models.talent_pools_pipelines import *
from candidate_pool_service.common.models.email_marketing import EmailCampaignSend
from candidate_pool_service.common.utils.talent_reporting import email_error_to_admins
from candidate_pool_service.common.models.smartlist import Smartlist
from candidate_pool_service.common.utils.auth_utils import require_oauth, require_all_roles
from candidate_pool_service.candidate_pool_app.talent_pools_pipelines_utilities import (TALENT_PIPELINE_SEARCH_PARAMS,
                                                                                        get_candidates_of_talent_pipeline)


talent_pipeline_blueprint = Blueprint('talent_pipeline_api', __name__)


class TalentPipelineApi(Resource):

    # Access token decorator
    decorators = [require_oauth()]

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
    decorators = [require_oauth()]

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
    decorators = [require_oauth()]

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

        return get_candidates_of_talent_pipeline(talent_pipeline)


@talent_pipeline_blueprint.route('/talent-pipelines/stats', methods=['POST'])
@require_oauth(allow_basic_auth=True, allow_null_user=True)
@require_all_roles('CAN_UPDATE_TALENT_PIPELINES_STATS')
def update_talent_pipelines_stats():
    """
    This method will update the statistics of all talent-pipelines daily.
    :return: None
    """
    try:
        talent_pipelines = TalentPipeline.query.all()
        for talent_pipeline in talent_pipelines:
            last_week_stat = TalentPipelineStats.query.filter_by(talent_pipeline_id=talent_pipeline.id).\
                order_by(TalentPipelineStats.id.desc()).first()

            # Return only candidate_ids
            response = get_candidates_of_talent_pipeline(talent_pipeline, 'id')
            total_candidates = response.get('total_found')
            talent_pipeline_candidate_ids = [candidate.get('id') for candidate in response.get('candidates')]
            engaged_candidates = len(db.session.query(EmailCampaignSend.candidate_id).filter(
                EmailCampaignSend.candidate_id.in_(talent_pipeline_candidate_ids)).all() or [])
            candidates_engagement = int(float(engaged_candidates)/total_candidates*100) if int(total_candidates) else 0
            # TODO: SMS_CAMPAIGNS are not implemented yet so we need to integrate them too here.

            if last_week_stat:
                talent_pipeline_stat = TalentPipelineStats(talent_pipeline_id=talent_pipeline.id,
                                                           total_candidates=total_candidates,
                                                           number_of_candidates_removed_or_added=
                                                           total_candidates - last_week_stat.total_candidates,
                                                           candidates_engagement=candidates_engagement)
            else:
                talent_pipeline_stat = TalentPipelineStats(talent_pipeline_id=talent_pipeline.id,
                                                           total_candidates=total_candidates,
                                                           number_of_candidates_removed_or_added=total_candidates,
                                                           candidates_engagement=candidates_engagement
                                                           )
            db.session.add(talent_pipeline_stat)

        db.session.commit()
        return '', 204

    except Exception as e:
        db.session.rollback()
        email_error_to_admins("Couldn't update statistics of TalentPipelines because: %s" % e.message,
                              subject="TalentPipeline Statistics")
        raise InvalidUsage(error_message="Couldn't update statistics of TalentPools because: %s" % e.message)


@talent_pipeline_blueprint.route('/talent-pipeline/<int:talent_pipeline_id>/stats', methods=['GET'])
@require_oauth()
def get_talent_pipeline_stats(talent_pipeline_id):
    """
    This method will return the statistics of a talent_pipeline over a given period of time with time-period = 1 day
    :param talent_pipeline_id: Id of a talent-pipeline
    :return: A list of time-series data
    """
    talent_pipeline = TalentPipeline.query.get(talent_pipeline_id)
    if not talent_pipeline:
        raise NotFoundError(error_message="TalentPipeline with id=%s doesn't exist in database" % talent_pipeline_id)

    if talent_pipeline.owner_user_id != request.user.id:
        raise ForbiddenError(error_message="Logged-in user %s is unauthorized to get stats of talent-pipeline %s"
                                           % (request.user.id, talent_pipeline.id))

    from_date_string = request.args.get('from_date', '')
    to_date_string = request.args.get('to_date', '')

    if not from_date_string and not to_date_string:
        raise InvalidUsage(error_message="Either 'from_date' or 'to_date' is missing from request parameters")

    try:
        from_date = parse(from_date_string)
        to_date = parse(to_date_string)
    except Exception as e:
        raise InvalidUsage(error_message="Either 'from_date' or 'to_date' is invalid because: %s" % e.message)

    talent_pipeline_stats = TalentPipelineStats.query.filter(
        TalentPipelineStats.talent_pipeline_id == talent_pipeline_id, TalentPipelineStats.added_time >= from_date,
        TalentPipelineStats.added_time <= to_date)

    return jsonify({'talent_pipeline_data': [
        {
            'total_number_of_candidates': talent_pipeline_stat.total_candidates,
            'number_of_candidates_removed_or_added': talent_pipeline_stat.number_of_candidates_removed_or_added,
            'added_time': talent_pipeline_stat.added_time,
            'candidates_engagement': talent_pipeline_stat.candidates_engagement
        }
        for talent_pipeline_stat in talent_pipeline_stats
    ]})

api = TalentApi(talent_pipeline_blueprint)
api.add_resource(TalentPipelineApi, '/talent-pipelines/<int:id>', '/talent-pipelines')
api.add_resource(TalentPipelineSmartListApi, '/talent-pipeline/<int:id>/smart_lists')
api.add_resource(TalentPipelineCandidates, '/talent-pipeline/<int:id>/candidates')
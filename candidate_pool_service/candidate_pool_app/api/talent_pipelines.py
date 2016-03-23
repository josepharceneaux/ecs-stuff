from candidate_pool_service.common.routes import CandidatePoolApi

__author__ = 'ufarooqi'

from flask import Blueprint
from dateutil import parser
from sqlalchemy import and_
from flask_restful import Resource
from dateutil.parser import parse
from candidate_pool_service.common.error_handling import *
from candidate_pool_service.common.talent_api import TalentApi
from candidate_pool_service.common.utils.validators import is_number
from candidate_pool_service.common.models.smartlist import Smartlist
from candidate_pool_service.common.models.user import DomainRole
from candidate_pool_service.common.models.talent_pools_pipelines import *
from candidate_pool_service.common.utils.auth_utils import require_oauth, require_all_roles
from candidate_pool_service.candidate_pool_app.talent_pools_pipelines_utilities import (get_pipeline_growth,
    TALENT_PIPELINE_SEARCH_PARAMS, get_candidates_of_talent_pipeline, get_stats_generic_function,
                                                                                         get_smartlist_stat_for_a_given_day)

talent_pipeline_blueprint = Blueprint('talent_pipeline_api', __name__)


class TalentPipelineApi(Resource):
    # Access token decorator
    decorators = [require_oauth()]

    @require_all_roles(DomainRole.Roles.CAN_GET_TALENT_PIPELINES)
    def get(self, **kwargs):
        """
        GET /talent-pipelines/<id>      Fetch talent-pipeline object
        GET /talent-pipelines           Fetch all talent-pipelines objects of domain of logged-in user

        :return A dictionary containing talent-pipeline's basic info or a dictionary containing all talent-pipelines of
        a domain

        :rtype: dict
        """

        talent_pipeline_id = kwargs.get('id')
        interval_in_days = request.args.get('interval', 30)

        if not is_number(interval_in_days) or int(interval_in_days) < 0:
            raise InvalidUsage("Value of interval should be positive integer")

        if talent_pipeline_id:
            talent_pipeline = TalentPipeline.query.get(talent_pipeline_id)

            if not talent_pipeline:
                raise NotFoundError(error_message="Talent pipeline with id %s doesn't exist in database" %
                                                  talent_pipeline_id)

            if talent_pipeline.user.domain_id != request.user.domain_id:
                raise ForbiddenError(error_message="Logged-in user and talent_pipeline belong to different domain")

            return {
                'talent_pipeline': talent_pipeline.to_dict(include_growth=True, interval=interval_in_days,
                                                           get_growth_function=get_pipeline_growth)
            }
        else:
            talent_pipelines = TalentPipeline.query.join(TalentPipeline.user).filter(User.domain_id ==
                                                                              request.user.domain_id).all()
            sort_by = request.args.get('sort_by', 'added_time')
            page = request.args.get('page', 1)
            per_page = request.args.get('per_page', 10)

            if talent_pipelines and sort_by not in ('growth', 'added_time'):
                raise InvalidUsage('Value of sort parameter is not valid')

            if not is_number(page) or not is_number(per_page) or int(page) < 1 or int(per_page) < 1:
                raise InvalidUsage("page and per_page should be positive integers")

            page = int(page)
            per_page = int(per_page)

            talent_pipelines_data = [talent_pipeline.to_dict(include_growth=True, interval=interval_in_days,
                                                             get_growth_function=get_pipeline_growth
                                                             ) for talent_pipeline in talent_pipelines
            ]
            talent_pipelines_data = sorted(talent_pipelines_data,
                                           key=lambda talent_pipeline_data: talent_pipeline_data[sort_by], reverse=True)
            return dict(talent_pipelines=talent_pipelines_data[(page - 1) * 10:page * 10], page_number=page,
                        talent_pipelines_per_page=per_page, total_number_of_talent_pipelines=len(talent_pipelines_data))

    @require_all_roles(DomainRole.Roles.CAN_DELETE_TALENT_PIPELINES)
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
            'talent_pipeline': {'id': talent_pipeline_id}
        }

    @require_all_roles(DomainRole.Roles.CAN_ADD_TALENT_PIPELINES)
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

            if parser.parse(date_needed) < datetime.utcnow():
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
                                             date_needed=date_needed, user_id=request.user.id,
                                             talent_pool_id=talent_pool_id, search_params=search_params)

            db.session.add(talent_pipeline)
            talent_pipeline_objects.append(talent_pipeline)

        db.session.commit()

        return {
            'talent_pipelines': [talent_pipeline_object.id for talent_pipeline_object in talent_pipeline_objects]
        }

    @require_all_roles(DomainRole.Roles.CAN_EDIT_TALENT_PIPELINES)
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

            if parser.parse(date_needed) < datetime.utcnow():
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

    @require_all_roles(DomainRole.Roles.CAN_GET_TALENT_PIPELINE_SMART_LISTS)
    def get(self, **kwargs):
        """
        GET /talent-pipeline/<id>/smart_lists   Fetch all smartlists of a talent_pipeline

        :return A dictionary containing smartlist objects of a talent_pipeline

        :rtype: dict
        """

        talent_pipeline_id = kwargs.get('id')

        talent_pipeline = TalentPipeline.query.get(talent_pipeline_id)

        if not talent_pipeline:
            raise NotFoundError(error_message="Talent pipeline with id %s doesn't exist in database" %
                                              talent_pipeline_id)

        if talent_pipeline.user.domain_id != request.user.domain_id:
            raise ForbiddenError(error_message="Logged-in user and talent_pipeline belong to different domain")

        page = request.args.get('page', 1)
        per_page = request.args.get('per_page', 10)

        if not is_number(page) or not is_number(per_page) or int(page) < 1 or int(per_page) < 1:
            raise InvalidUsage("page and per_page should be positive integers")

        page = int(page)
        per_page = int(per_page)

        total_number_of_smartlists = Smartlist.query.filter_by(talent_pipeline_id=talent_pipeline_id).count()
        smartlists = Smartlist.query.filter_by(talent_pipeline_id=talent_pipeline_id).paginate(page, per_page, False)
        smartlists = smartlists.items

        return {
            'page_number': page, 'smartlists_per_page': per_page,
            'total_number_of_smartlists': total_number_of_smartlists,
            'smartlists': [smartlist.to_dict(True, get_stats_generic_function) for smartlist in smartlists]
        }

    @require_all_roles(DomainRole.Roles.CAN_ADD_TALENT_PIPELINE_SMART_LISTS)
    def post(self, **kwargs):
        """
        POST /talent-pipeline/<id>/smartlists   Add smartlists to a talent_pipeline

        Take a JSON dictionary containing smartlist_ids

        :return A dictionary containing smartlist_ids successfully added to talent_pipeline

        :rtype: dict
        """

        talent_pipeline_id = kwargs.get('id')

        talent_pipeline = TalentPipeline.query.get(talent_pipeline_id)

        if not talent_pipeline:
            raise NotFoundError(error_message="Talent pipeline with id %s doesn't exist in database" %
                                              talent_pipeline_id)

        posted_data = request.get_json(silent=True)
        if not posted_data or 'smartlist_ids' not in posted_data:
            raise InvalidUsage(error_message="Request body is empty or not provided")

        # Save user object(s)
        smartlist_ids = posted_data['smartlist_ids']

        # Talent_pool object(s) must be in a list
        if not isinstance(smartlist_ids, list):
            raise InvalidUsage(error_message="Request body is not properly formatted")

        if talent_pipeline.user.domain_id != request.user.domain_id:
            raise ForbiddenError(error_message="Logged-in user and talent_pipeline belong to different domain")

        for smartlist_id in smartlist_ids:

            if not is_number(smartlist_id):
                raise InvalidUsage('Smartlist id %s should be an integer' % smartlist_id)
            else:
                smartlist_id = int(smartlist_id)

            smartlist = Smartlist.query.get(smartlist_id)

            if smartlist.user.domain_id != talent_pipeline.user.domain_id:
                raise ForbiddenError(error_message="Smartlist %s and Talent pipeline %s belong to different domain"
                                                   % (smartlist_id, talent_pipeline_id))

            if smartlist.talent_pipeline_id == talent_pipeline_id:
                raise InvalidUsage(error_message="Smartlist %s already belongs to Talent Pipeline %s"
                                                 % (smartlist.name, talent_pipeline_id))

            if smartlist.talent_pipeline_id:
                raise ForbiddenError(error_message="smartlist %s is already assigned to talent_pipeline %s" %
                                                   (smartlist.name, smartlist.talent_pipeline_id))

            smartlist.talent_pipeline_id = talent_pipeline_id

        db.session.commit()

        return {
            'smartlist_ids': [int(smartlist_id) for smartlist_id in smartlist_ids]
        }

    @require_all_roles(DomainRole.Roles.CAN_DELETE_TALENT_PIPELINE_SMART_LISTS)
    def delete(self, **kwargs):
        """
        DELETE /talent-pipeline/<id>/smartlists   Remove smartlists from a talent_pipeline

        Take a JSON dictionary containing smartlist_ids

        :return A dictionary containing smartlist_ids successfully removed from a talent_pipeline

        :rtype: dict
        """

        talent_pipeline_id = kwargs.get('id')

        talent_pipeline = TalentPipeline.query.get(talent_pipeline_id)

        if not talent_pipeline:
            raise NotFoundError(error_message="Talent pipeline with id %s doesn't exist in database" %
                                              talent_pipeline_id)

        posted_data = request.get_json(silent=True)
        if not posted_data or 'smartlist_ids' not in posted_data:
            raise InvalidUsage(error_message="Request body is empty or not provided")

        # Save user object(s)
        smartlist_ids = posted_data['smartlist_ids']

        # Talent_pool object(s) must be in a list
        if not isinstance(smartlist_ids, list):
            raise InvalidUsage(error_message="Request body is not properly formatted")

        if talent_pipeline.user.domain_id != request.user.domain_id:
            raise ForbiddenError(error_message="Logged-in user and talent_pipeline belong to different domain")

        for smartlist_id in smartlist_ids:

            if not is_number(smartlist_id):
                raise InvalidUsage('Smart List id %s should be an integer' % smartlist_id)
            else:
                smartlist_id = int(smartlist_id)

            smartlist = Smartlist.query.get(smartlist_id)

            if smartlist.talent_pipeline_id != talent_pipeline_id:
                raise ForbiddenError(error_message="smartlist %s doesn't belong to talent_pipeline %s" %
                                                   (smartlist.name, talent_pipeline_id))

            smartlist.talent_pipeline_id = None

        db.session.commit()

        return {
            'smartlist_ids': [int(smartlist_id) for smartlist_id in smartlist_ids]
        }


class TalentPipelineCandidates(Resource):
    # Access token decorator
    decorators = [require_oauth()]

    @require_all_roles(DomainRole.Roles.CAN_GET_TALENT_PIPELINE_CANDIDATES)
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

        request_params = dict()
        request_params['fields'] = request.args.get('fields', '')
        request_params['sort_by'] = request.args.get('sort_by', '')
        request_params['limit'] = request.args.get('limit', '')
        request_params['page'] = request.args.get('page', '')

        return get_candidates_of_talent_pipeline(talent_pipeline, request.oauth_token, request_params=request_params)


class TalentPipelineCampaigns(Resource):
    # Access token decorator
    decorators = [require_oauth()]

    # TODO: Add Role here for CAN_GET_EMAIL_CAMPAIGNS once it becomes available, and CAN_GET_TALENT_PIPELINE_SMART_LISTS.
    # @require_all_roles(DomainRole.Roles.CAN_GET_TALENT_PIPELINE_SMART_LISTS)
    def get(self, **kwargs):
        """
        GET /talent-pipelines/<id>/campaigns?fields=id,subject&page=1&per_page=20

        Fetch all campaigns of a talent-pipeline.

        :return A dictionary containing list of campaigns belonging to a talent-pipeline
        :rtype: dict
        """

        # Valid talent pipeline
        talent_pipeline_id = kwargs.get('id')
        talent_pipeline = TalentPipeline.query.get(talent_pipeline_id)
        if not talent_pipeline:
            raise NotFoundError("Talent pipeline with id %s doesn't exist in database" % talent_pipeline_id)
        if talent_pipeline.user.domain_id != request.user.domain_id:
            raise ForbiddenError("Logged-in user and talent_pipeline belong to different domain")

        # Get the email campaigns
        include_fields = request.values['fields'].split(',') if request.values.get('fields') else None
        email_campaigns = talent_pipeline.get_email_campaigns(page=request.values.get('page', 1),
                                                              per_page=request.values.get('per_page', 20))
        return {'email_campaigns': [email_campaign.to_dict(include_fields) for email_campaign in email_campaigns]}


@talent_pipeline_blueprint.route(CandidatePoolApi.TALENT_PIPELINE_GET_STATS, methods=['GET'])
@require_oauth(allow_null_user=True)
def get_talent_pipeline_stats(talent_pipeline_id):
    """
    This method will return the statistics of a talent_pipeline over a given period of time with time-period = 1 day
    :param talent_pipeline_id: Id of a talent-pipeline
    :return: A list of time-series data
    """
    from_date_string = request.args.get('from_date', '')
    to_date_string = request.args.get('to_date', '')
    interval = request.args.get('interval', '1')
    talent_pipeline = TalentPipeline.query.get(talent_pipeline_id)
    response = get_stats_generic_function(talent_pipeline, 'TalentPipeline', request.user, from_date_string,
                                          to_date_string, interval)
    if 'is_update' in request.args:
        return '', 204
    else:
        return jsonify({'talent_pipeline_data': response})


@talent_pipeline_blueprint.route(CandidatePoolApi.SMARTLIST_IN_TALENT_PIPELINE_GET_STATS, methods=['GET'])
@require_oauth()
def get_smartlists_in_talent_pipeline_stats(talent_pipeline_id):
    """
    This method will return the statistics of all smartlists in a talent_pipeline over a given period of time
    with time-period = 1 day
    :param talent_pipeline_id: Id of a talent-pipeline
    :return: A list of time-series data
    """
    talent_pipeline = TalentPipeline.query.get(talent_pipeline_id)
    if not talent_pipeline:
        raise NotFoundError(error_message="TalentPipeline with id=%s doesn't exist in database" % talent_pipeline_id)

    if talent_pipeline.user.domain_id != request.user.domain_id:
        raise ForbiddenError(error_message="Logged-in user %s is unauthorized to get stats of talent-pipeline %s"
                                           % (request.user.id, talent_pipeline_id))

    from_date_string = request.args.get('from_date', '')
    to_date_string = request.args.get('to_date', '')
    interval = request.args.get('interval', '1')

    try:
        from_date = parse(from_date_string).date() if from_date_string else talent_pipeline.added_time.date()
        to_date = parse(to_date_string).date() if to_date_string else datetime.utcnow().date()
    except Exception as e:
        raise InvalidUsage(error_message="Either 'from_date' or 'to_date' is invalid because: %s" % e.message)

    if from_date < talent_pipeline.added_time.date():
        from_date = talent_pipeline.added_time.date()

    if from_date > to_date:
        raise InvalidUsage("`to_date` cannot come before `from_date`")

    if to_date > datetime.utcnow().date():
        raise InvalidUsage("`to_date` cannot be in future")

    if not is_number(interval):
        raise InvalidUsage("Interval '%s' should be integer" % interval)

    interval = int(interval)
    if interval < 1:
        raise InvalidUsage("Interval's value should be greater than or equal to 1 day")

    smartlists_of_talent_pipeline = Smartlist.query.filter(Smartlist.talent_pipeline_id == talent_pipeline_id).all()
    talent_pipeline_stats = []

    from_date -= timedelta(days=interval)
    while to_date >= from_date:
        total_number_of_candidates = 0
        for smartlist in smartlists_of_talent_pipeline:
            total_number_of_candidates += get_smartlist_stat_for_a_given_day(smartlist, to_date)

        talent_pipeline_stats.append({
            'total_number_of_candidates': total_number_of_candidates,
            'added_datetime': to_date.isoformat(),
        })
        to_date -= timedelta(days=interval)

    reference_talent_pipeline_stat = talent_pipeline_stats.pop()
    for index, talent_pipeline_stat in enumerate(talent_pipeline_stats):
        talent_pipeline_stat['number_of_candidates_added'] = talent_pipeline_stat['total_number_of_candidates'] - (
                talent_pipeline_stats[index + 1]['total_number_of_candidates'] if index + 1 < len(
                        talent_pipeline_stats) else reference_talent_pipeline_stat['total_number_of_candidates'])

    return jsonify({'talent_pipeline_data': talent_pipeline_stats})


api = TalentApi(talent_pipeline_blueprint)
api.add_resource(TalentPipelineApi, CandidatePoolApi.TALENT_PIPELINE, CandidatePoolApi.TALENT_PIPELINES)
api.add_resource(TalentPipelineSmartListApi, CandidatePoolApi.TALENT_PIPELINE_SMARTLISTS)
api.add_resource(TalentPipelineCandidates, CandidatePoolApi.TALENT_PIPELINE_CANDIDATES)
api.add_resource(TalentPipelineCampaigns, CandidatePoolApi.TALENT_PIPELINE_CAMPAIGNS)
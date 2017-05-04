from candidate_pool_service.common.routes import CandidatePoolApi

__author__ = 'ufarooqi'

from flask import Blueprint
from dateutil import parser
from flask_restful import Resource
from candidate_pool_service.common.error_handling import *
from candidate_pool_service.common.talent_api import TalentApi
from candidate_pool_service.common.utils.validators import is_number
from candidate_pool_service.common.models.smartlist import Smartlist
from candidate_pool_service.common.models.user import Permission
from candidate_pool_service.common.models.candidate_edit import CandidateEdit
from candidate_pool_service.common.models.misc import Activity
from candidate_pool_service.common.models.talent_pools_pipelines import *
from candidate_pool_service.common.utils.auth_utils import require_oauth, require_all_permissions
from candidate_pool_service.common.utils.api_utils import ApiResponse, generate_pagination_headers
from candidate_pool_service.candidate_pool_app.talent_pools_pipelines_utilities import (
    TALENT_PIPELINE_SEARCH_PARAMS, get_candidates_of_talent_pipeline, get_pipeline_engagement_score,
    get_stats_generic_function, top_most_engaged_candidates_of_pipeline, top_most_engaged_pipelines_of_candidate,
    get_talent_pipeline_stat_for_given_day)
from candidate_pool_service.common.utils.api_utils import DEFAULT_PAGE, DEFAULT_PAGE_SIZE
from candidate_pool_service.common.inter_service_calls.candidate_service_calls import update_candidates_on_cloudsearch
from candidate_pool_service.common.inter_service_calls.activity_service_calls import add_activity

talent_pipeline_blueprint = Blueprint('talent_pipeline_api', __name__)
EPOCH_TIME_STRING = '1969-12-31'


class TalentPipelineApi(Resource):
    # Access token decorator
    decorators = [require_oauth()]

    @require_all_permissions(Permission.PermissionNames.CAN_GET_TALENT_PIPELINES)
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
        candidate_count = request.args.get('candidate-count', False)
        email_campaign_count = request.args.get('email-campaign-count', False)

        if not is_number(candidate_count) or int(candidate_count) not in (True, False):
            raise InvalidUsage("`candidate_count` field value can be 0 or 1")

        if not is_number(email_campaign_count) or int(email_campaign_count) not in (True, False):
            raise InvalidUsage("`email_campaign_count` field value can be 0 or 1")

        if not is_number(interval_in_days) or int(interval_in_days) < 0:
            raise InvalidUsage("Value of interval should be positive integer")

        if talent_pipeline_id:
            talent_pipeline = TalentPipeline.query.get(talent_pipeline_id)

            if not talent_pipeline:
                raise NotFoundError("Talent pipeline with id {} doesn't exist in database".format(talent_pipeline_id))

            if request.user.role.name != 'TALENT_ADMIN' and talent_pipeline.user.domain_id != request.user.domain_id:
                raise ForbiddenError("Logged-in user and talent_pipeline belong to different domain")

            if not candidate_count:
                talent_pipeline_dict = talent_pipeline.to_dict(email_campaign_count=email_campaign_count)
            else:
                talent_pipeline_dict = talent_pipeline.to_dict(email_campaign_count=email_campaign_count,
                                                               include_candidate_count=True,
                                                               get_candidate_count=get_talent_pipeline_stat_for_given_day)

            talent_pipeline_dict.update({'engagement_score': get_pipeline_engagement_score(talent_pipeline_id)})
            return {'talent_pipeline': talent_pipeline_dict}

        else:
            sort_by = request.args.get('sort_by', 'added_time')
            sort_type = request.args.get('sort_type', 'DESC')
            search_keyword = request.args.get('search', '').strip()
            owner_user_id = request.args.get('user_id', '')
            is_hidden = request.args.get('is_hidden', 0)
            from_date = request.args.get('from_date', EPOCH_TIME_STRING)
            to_date = request.args.get('to_date', datetime.utcnow().isoformat())
            page = request.args.get('page', DEFAULT_PAGE)
            per_page = request.args.get('per_page', DEFAULT_PAGE_SIZE)

            if not is_number(is_hidden) or int(is_hidden) not in (0, 1):
                raise InvalidUsage('`is_hidden` can be either 0 or 1')

            if not is_number(page) or not is_number(per_page) or int(page) < 1 or int(per_page) < 1:
                raise InvalidUsage("page and per_page should be positive integers")

            page = int(page)
            per_page = int(per_page)

            if owner_user_id and is_number(owner_user_id) and not User.query.get(int(owner_user_id)):
                raise InvalidUsage("User: (%s) doesn't exist in system")

            if sort_by not in ('added_time', 'name', 'engagement_score'):
                raise InvalidUsage('Value of sort parameter is not valid')

            try:
                from_date = parser.parse(from_date).replace(tzinfo=None)
                to_date = parser.parse(from_date).replace(tzinfo=None)
            except Exception as e:
                raise InvalidUsage("from_date or to_date is not properly formatted: %s" % e)

            if owner_user_id:
                talent_pipelines_query = TalentPipeline.query.join(User).filter(and_(
                    TalentPipeline.is_hidden == is_hidden, User.id == int(owner_user_id),
                        from_date <= TalentPipeline.added_time <= to_date, or_(TalentPipeline.name.ilike(
                                '%' + search_keyword + '%'), TalentPipeline.description.ilike(
                                '%' + search_keyword + '%'))))
            else:
                talent_pipelines_query = TalentPipeline.query.join(User).filter(and_(
                    TalentPipeline.is_hidden == is_hidden, User.domain_id == request.user.domain_id,
                        from_date <= TalentPipeline.added_time <= to_date, or_(
                                TalentPipeline.name.ilike('%' + search_keyword + '%'),
                                TalentPipeline.description.ilike('%' + search_keyword + '%'))))

            total_number_of_talent_pipelines = talent_pipelines_query.count()

            if sort_by not in ("engagement_score", "candidate_count"):
                if sort_by == 'added_time':
                    sort_attribute = TalentPipeline.added_time
                else:
                    sort_attribute = TalentPipeline.name
                talent_pipelines = talent_pipelines_query.order_by(
                    sort_attribute.asc() if sort_type == 'ASC' else sort_attribute.desc()).paginate(page, per_page,
                                                                                                    False)
                talent_pipelines = talent_pipelines.items
            else:
                talent_pipelines = talent_pipelines_query.all()

            if candidate_count or sort_by == "candidate_count":
                talent_pipelines_data = [
                    talent_pipeline.to_dict(include_cached_candidate_count=True,
                                            email_campaign_count=email_campaign_count,
                                            get_candidate_count=get_talent_pipeline_stat_for_given_day)
                    for talent_pipeline in talent_pipelines]
            else:
                talent_pipelines_data = [
                    talent_pipeline.to_dict(email_campaign_count=email_campaign_count)
                    for talent_pipeline in talent_pipelines]

            for talent_pipeline_data in talent_pipelines_data:
                talent_pipeline_data['engagement_score'] = get_pipeline_engagement_score(talent_pipeline_data['id'])

            if sort_by in ("engagement_score", "candidate_count"):
                sort_by = 'total_candidates' if sort_by == "candidate_count" else "engagement_score"
                talent_pipelines_data = sorted(
                        talent_pipelines_data, key=lambda talent_pipeline_data: talent_pipeline_data[sort_by],
                        reverse=(False if sort_type == 'ASC' else True))
                talent_pipelines_data = talent_pipelines_data[(page - 1) * per_page:page * per_page]

            headers = generate_pagination_headers(total_number_of_talent_pipelines, per_page, page)

            response = dict(
                talent_pipelines=talent_pipelines_data,
                page_number=page, talent_pipelines_per_page=per_page,
                total_number_of_talent_pipelines=total_number_of_talent_pipelines
            )

            return ApiResponse(response=response, headers=headers, status=200)

    @require_all_permissions(Permission.PermissionNames.CAN_DELETE_TALENT_PIPELINES)
    def delete(self, **kwargs):
        """
        DELETE /talent-pipelines/<id>  Remove talent-pipeline from Database

        :return A dictionary containing deleted talent-pipeline's id

        :rtype: dict
        """

        talent_pipeline_id = kwargs.get('id')

        if not talent_pipeline_id:
            raise InvalidUsage("A valid talent_pipeline_id should be provided")

        talent_pipeline = TalentPipeline.query.get(talent_pipeline_id)
        if not talent_pipeline:
            raise NotFoundError("Talent pipeline with id {} doesn't exist in database".format(talent_pipeline_id))

        if request.user.role.name == 'USER' and talent_pipeline.user.id != request.user.id:
            raise ForbiddenError("Logged-in user doesn't have appropriate permissions to delete this talent-pipeline")

        if request.user.role.name != 'TALENT_ADMIN' and talent_pipeline.user.domain_id != request.user.domain_id:
            raise ForbiddenError("Logged-in user and talent_pipeline belong to different domain")

        talent_pipeline.is_hidden = 1
        db.session.commit()

        return {
            'talent_pipeline': {'id': talent_pipeline_id}
        }

    @require_all_permissions(Permission.PermissionNames.CAN_ADD_TALENT_PIPELINES)
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
            raise InvalidUsage("Request body is empty or not provided")

        # Save user object(s)
        talent_pipelines = posted_data['talent_pipelines']

        # TalentPipeline object(s) must be in a list
        if not isinstance(talent_pipelines, list):
            raise InvalidUsage("Request body is not properly formatted")

        talent_pipeline_objects = []
        for talent_pipeline in talent_pipelines:

            name = talent_pipeline.get('name', '')
            description = talent_pipeline.get('description', '')
            positions = talent_pipeline.get('positions', 1)
            date_needed = talent_pipeline.get('date_needed', '')
            talent_pool_id = talent_pipeline.get('talent_pool_id', '')
            search_params = talent_pipeline.get('search_params', dict())

            if not name or not date_needed or not talent_pool_id:
                raise InvalidUsage("A valid name, date_needed, talent_pool_id should be provided to "
                                   "create a new talent-pipeline")

            if TalentPipeline.query.join(TalentPipeline.user).filter(and_(
                            TalentPipeline.name == name, User.domain_id == request.user.domain_id)).first():
                raise InvalidUsage(
                    "Talent pipeline with name {} already exists in domain {}".format(name, request.user.domain_id))

            try:
                date_needed = parser.parse(date_needed)
            except Exception as e:
                raise InvalidUsage("Date_needed is not valid as: {}".format(e.message))

            if not is_number(positions) or not int(positions) > 0:
                raise InvalidUsage("Number of positions should be integer and greater than zero")

            if not is_number(talent_pool_id):
                raise InvalidUsage("talent_pool_id should be an integer")

            talent_pool_id = int(talent_pool_id)
            talent_pool = TalentPool.query.get(talent_pool_id)
            if not talent_pool:
                raise NotFoundError("Talent pool with id {} doesn't exist in database".format(talent_pool_id))

            if talent_pool.domain_id != request.user.domain_id:
                raise ForbiddenError("Logged-in user and given talent-pool belong to different domain")

            if search_params:
                if not isinstance(search_params, dict):
                    raise InvalidUsage("search_params is not provided in valid format")

                # Put into params dict
                for key in search_params:
                    if key not in TALENT_PIPELINE_SEARCH_PARAMS and not key.startswith('cf-'):
                        raise NotFoundError("Key[{}] is invalid".format(key))

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

    @require_all_permissions(Permission.PermissionNames.CAN_EDIT_TALENT_PIPELINES)
    def put(self, **kwargs):
        """
        PUT /talent-pipelines/<id>  Edit existing talent-pipeline

        Take a JSON dictionary containing TalentPipeline dictionary

        :return A dictionary containing id of edited talent-pipeline

        :rtype: dict
        """

        talent_pipeline_id = kwargs.get('id')

        if not talent_pipeline_id:
            raise InvalidUsage("A valid talent_pipeline_id should be provided")

        talent_pipeline = TalentPipeline.query.get(talent_pipeline_id)
        if not talent_pipeline:
            raise NotFoundError("Talent pipeline with id {} doesn't exist in database".format(talent_pipeline_id))

        if request.user.role.name == 'USER' and talent_pipeline.user.id != request.user.id:
            raise ForbiddenError("Logged-in user doesn't have appropriate permissions to edit this talent-pipeline")

        if request.user.role.name != 'TALENT_ADMIN' and talent_pipeline.user.domain_id != request.user.domain_id:
            raise ForbiddenError("Logged-in user and talent_pipeline belong to different domain")

        posted_data = request.get_json(silent=True)
        if not posted_data or 'talent_pipeline' not in posted_data:
            raise InvalidUsage("Request body is empty or not provided")
        posted_data = posted_data['talent_pipeline']

        name = posted_data.get('name')
        description = posted_data.get('description', '')
        positions = posted_data.get('positions', '')
        date_needed = posted_data.get('date_needed', '')
        talent_pool_id = posted_data.get('talent_pool_id', '')
        is_hidden = posted_data.get('is_hidden', 0)
        search_params = posted_data.get('search_params', dict())

        if name is not None:
            if name:
                if TalentPipeline.query.join(TalentPipeline.user).filter(
                        and_(TalentPipeline.name == name, User.domain_id == request.user.domain_id)).first():
                    raise InvalidUsage("Talent pipeline with name {} already exists in domain {}".format(
                        name, request.user.domain_id))
                talent_pipeline.name = name
            else:
                raise InvalidUsage("Name cannot be an empty string")

        if date_needed:
            try:
                parser.parse(date_needed)
            except Exception as e:
                raise InvalidUsage("Date_needed is not valid as: {}".format(e.message))

            if parser.parse(date_needed) < datetime.utcnow():
                raise InvalidUsage("Date_needed {} cannot be before current date".format(date_needed))

            talent_pipeline.date_needed = date_needed

        if positions:
            if not is_number(positions) or not int(positions) > 0:
                raise InvalidUsage("Number of positions should be integer and greater than zero")

            talent_pipeline.positions = positions

        if description:
            talent_pipeline.description = description

        if talent_pool_id:

            if not is_number(talent_pool_id):
                raise InvalidUsage("talent_pool_id should be an integer")

            talent_pool_id = int(talent_pool_id)
            talent_pool = TalentPool.query.get(talent_pool_id)
            if not talent_pool:
                raise NotFoundError("Talent pool with id {} doesn't exist in database".format(talent_pool_id))

            if talent_pool.domain_id != request.user.domain_id:
                raise ForbiddenError("Logged-in user and given talent-pool belong to different domain")

            talent_pipeline.talent_pool_id = talent_pool_id

        if search_params:
            if not isinstance(search_params, dict):
                raise InvalidUsage("search_params is not provided in valid format")

            # Put into params dict
            for key in search_params:
                if key not in TALENT_PIPELINE_SEARCH_PARAMS and not key.startswith('cf-'):
                    raise NotFoundError("Key[{}] is invalid".format(key))

            talent_pipeline.search_params = json.dumps(search_params)

        if not is_number(is_hidden) or (int(is_hidden) not in (0, 1)):
            raise InvalidUsage("Possible vaues of `is_hidden` are 0 and 1")

        talent_pipeline.is_hidden = int(is_hidden)

        db.session.commit()

        return {
            'talent_pipeline': {'id': talent_pipeline.id}
        }


class TalentPipelineSmartListApi(Resource):
    # Access token decorator
    decorators = [require_oauth()]

    @require_all_permissions(Permission.PermissionNames.CAN_GET_TALENT_PIPELINES)
    def get(self, **kwargs):
        """
        GET /talent-pipeline/<id>/smart_lists   Fetch all smartlists of a talent_pipeline

        :return A dictionary containing smartlist objects of a talent_pipeline

        :rtype: dict
        """

        talent_pipeline_id = kwargs.get('id')

        talent_pipeline = TalentPipeline.query.get(talent_pipeline_id)

        if not talent_pipeline:
            raise NotFoundError("Talent pipeline with id {} doesn't exist in database".format(talent_pipeline_id))

        if request.user.role.name != 'TALENT_ADMIN' and talent_pipeline.user.domain_id != request.user.domain_id:
            raise ForbiddenError("Logged-in user and talent_pipeline belong to different domain")

        page = request.args.get('page', DEFAULT_PAGE)
        per_page = request.args.get('per_page', DEFAULT_PAGE_SIZE)

        if not is_number(page) or not is_number(per_page) or int(page) < 1 or int(per_page) < 1:
            raise InvalidUsage("page and per_page should be positive integers")

        page = int(page)
        per_page = int(per_page)

        total_number_of_smartlists = Smartlist.query.filter_by(talent_pipeline_id=talent_pipeline_id).count()
        smartlists = Smartlist.query.filter_by(talent_pipeline_id=talent_pipeline_id).order_by(
            Smartlist.added_time.desc()).paginate(page, per_page, False)

        smartlists = smartlists.items

        headers = generate_pagination_headers(total_number_of_smartlists, per_page, page)

        response = {
            'page_number': page, 'smartlists_per_page': per_page,
            'total_number_of_smartlists': total_number_of_smartlists,
            'smartlists': [smartlist.to_dict() for smartlist in smartlists]
        }

        return ApiResponse(response=response, headers=headers, status=200)

    @require_all_permissions(Permission.PermissionNames.CAN_EDIT_TALENT_PIPELINES)
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
            raise NotFoundError("Talent pipeline with id {} doesn't exist in database".format(talent_pipeline_id))

        posted_data = request.get_json(silent=True)
        if not posted_data or 'smartlist_ids' not in posted_data:
            raise InvalidUsage("Request body is empty or not provided")

        # Save user object(s)
        smartlist_ids = posted_data['smartlist_ids']

        # Talent_pool object(s) must be in a list
        if not isinstance(smartlist_ids, list):
            raise InvalidUsage("Request body is not properly formatted")

        if request.user.role.name == 'USER' and talent_pipeline.user.id != request.user.id:
            raise ForbiddenError("Logged-in user doesn't have appropriate permissions to edit this talent-pipeline")

        if request.user.role.name != 'TALENT_ADMIN' and talent_pipeline.user.domain_id != request.user.domain_id:
            raise ForbiddenError("Logged-in user and talent_pipeline belong to different domain")

        for smartlist_id in smartlist_ids:

            if not is_number(smartlist_id):
                raise InvalidUsage('Smartlist id %s should be an integer'.format(smartlist_id))
            else:
                smartlist_id = int(smartlist_id)

            smartlist = Smartlist.query.get(smartlist_id)

            if smartlist.user.domain_id != talent_pipeline.user.domain_id:
                raise ForbiddenError("Smartlist {} and Talent pipeline {} belong to different domain".format(
                    smartlist_id, talent_pipeline_id))

            if smartlist.talent_pipeline_id == talent_pipeline_id:
                raise InvalidUsage("Smartlist {} already belongs to Talent Pipeline {}".format(
                    smartlist.name, talent_pipeline_id))

            if smartlist.talent_pipeline_id:
                raise ForbiddenError("smartlist {} is already assigned to talent_pipeline {}".format(
                    smartlist.name, smartlist.talent_pipeline_id))

            smartlist.talent_pipeline_id = talent_pipeline_id

        db.session.commit()

        return {
            'smartlist_ids': [int(smartlist_id) for smartlist_id in smartlist_ids]
        }

    @require_all_permissions(Permission.PermissionNames.CAN_EDIT_TALENT_PIPELINES)
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
            raise NotFoundError("Talent pipeline with id {} doesn't exist in database".format(talent_pipeline_id))

        posted_data = request.get_json(silent=True)
        if not posted_data or 'smartlist_ids' not in posted_data:
            raise InvalidUsage("Request body is empty or not provided")

        # Save user object(s)
        smartlist_ids = posted_data['smartlist_ids']

        # Talent_pool object(s) must be in a list
        if not isinstance(smartlist_ids, list):
            raise InvalidUsage("Request body is not properly formatted")

        if request.user.role.name == 'USER' and talent_pipeline.user.id != request.user.id:
            raise ForbiddenError("Logged-in user doesn't have appropriate permissions to edit this talent-pipeline")

        if request.user.role.name != 'TALENT_ADMIN' and talent_pipeline.user.domain_id != request.user.domain_id:
            raise ForbiddenError("Logged-in user and talent_pipeline belong to different domain")

        for smartlist_id in smartlist_ids:

            if not is_number(smartlist_id):
                raise InvalidUsage('Smart List id {} should be an integer'.format(smartlist_id))
            else:
                smartlist_id = int(smartlist_id)

            smartlist = Smartlist.query.get(smartlist_id)

            if smartlist.talent_pipeline_id != talent_pipeline_id:
                raise ForbiddenError("smartlist {} doesn't belong to talent_pipeline {}".format(
                    smartlist.name, talent_pipeline_id))

            smartlist.talent_pipeline_id = None

        db.session.commit()

        return {
            'smartlist_ids': [int(smartlist_id) for smartlist_id in smartlist_ids]
        }


class TalentPipelineCandidates(Resource):
    # Access token decorator
    decorators = [require_oauth()]

    @require_all_permissions(Permission.PermissionNames.CAN_ADD_TALENT_PIPELINES)
    def post(self, **kwargs):
        """
        POST /talent-pipeline/<id>/candidates  Add candidates to a Talent Pipeline
        :return None

        :rtype: None
        """
        talent_pipeline_id = kwargs.get('id')

        talent_pipeline = TalentPipeline.query.get(talent_pipeline_id)

        if not talent_pipeline:
            raise NotFoundError("Talent pipeline with id {} doesn't exist in database".format(talent_pipeline_id))

        posted_data = request.get_json(silent=True)
        if not posted_data or 'candidate_ids' not in posted_data:
            raise InvalidUsage("Request body is empty or not provided")

        candidate_ids = posted_data.get('candidate_ids')

        candidate_ids = list(set(candidate_ids))

        if Candidate.query.filter(Candidate.id.in_(candidate_ids)).count() != len(candidate_ids):
            raise InvalidUsage("Some of the candidates don't exist in DB")

        TalentPipelineExcludedCandidates.query.filter(
            TalentPipelineExcludedCandidates.talent_pipeline_id == talent_pipeline.id,
            TalentPipelineExcludedCandidates.candidate_id.in_(candidate_ids)).delete(synchronize_session='fetch')

        added_candidate_ids = []
        for candidate_id in candidate_ids:
            if not TalentPipelineIncludedCandidates.query.filter_by(talent_pipeline_id=talent_pipeline.id,
                                                                    candidate_id=candidate_id).first():
                added_candidate_ids.append(candidate_id)
                db.session.add(TalentPipelineIncludedCandidates(talent_pipeline_id=talent_pipeline.id,
                                                                candidate_id=candidate_id))

                # Track updates made to candidate's records
                db.session.add(CandidateEdit(
                    user_id=request.user.id,
                    candidate_id=candidate_id,
                    field_id=1801,
                    old_value=None,
                    new_value=talent_pipeline.name,
                    edit_datetime=datetime.utcnow(),
                    is_custom_field=False
                ))
            else:
                db.session.rollback()
                raise InvalidUsage("Candidate: %s is already included in pipeline: %s" % (
                    candidate_id, talent_pipeline.id))

        db.session.commit()

        update_candidates_on_cloudsearch(request.oauth_token, candidate_ids)

        activity_data = {
            'name': talent_pipeline.name
        }
        candidates = Candidate.query.with_entities(Candidate.id, Candidate.formatted_name).filter(
            Candidate.id.in_(added_candidate_ids)).all()

        for candidate_id, formatted_name in candidates:
            activity_data['formattedName'] = formatted_name
            add_activity(user_id=request.user.id, activity_type=Activity.MessageIds.PIPELINE_ADD_CANDIDATE,
                         source_table=Candidate.__tablename__, source_id=candidate_id, params=activity_data)

        return '', 204

    @require_all_permissions(Permission.PermissionNames.CAN_ADD_TALENT_PIPELINES)
    def delete(self, **kwargs):
        """
        DELETE /talent-pipeline/<id>/candidates  Add candidates to a Talent Pipeline
        :return None

        :rtype: None
        """
        talent_pipeline_id = kwargs.get('id')

        talent_pipeline = TalentPipeline.query.get(talent_pipeline_id)

        if not talent_pipeline:
            raise NotFoundError("Talent pipeline with id {} doesn't exist in database".format(talent_pipeline_id))

        posted_data = request.get_json(silent=True)
        if not posted_data or 'candidate_ids' not in posted_data:
            raise InvalidUsage("Request body is empty or not provided")

        candidate_ids = posted_data.get('candidate_ids')

        candidate_ids = list(set(candidate_ids))

        if Candidate.query.filter(Candidate.id.in_(candidate_ids)).count() != len(candidate_ids):
            raise InvalidUsage("Some of the candidates don't exist in DB")

        TalentPipelineIncludedCandidates.query.filter(
            TalentPipelineIncludedCandidates.talent_pipeline_id == talent_pipeline.id,
            TalentPipelineIncludedCandidates.candidate_id.in_(candidate_ids)).delete(synchronize_session='fetch')

        removed_candidate_ids = []
        for candidate_id in candidate_ids:
            if not TalentPipelineExcludedCandidates.query.filter_by(talent_pipeline_id=talent_pipeline.id,
                                                                    candidate_id=candidate_id).first():
                removed_candidate_ids.append(candidate_id)

                db.session.add(TalentPipelineExcludedCandidates(talent_pipeline_id=talent_pipeline.id,
                                                                candidate_id=candidate_id))

                # Track updates made to candidate's records
                db.session.add(CandidateEdit(
                    user_id=request.user.id,
                    candidate_id=candidate_id,
                    field_id=1801,
                    old_value=talent_pipeline.name,
                    new_value=None,  # inferring deletion
                    edit_datetime=datetime.utcnow(),
                    is_custom_field=False
                ))
            else:
                db.session.rollback()
                raise InvalidUsage("Candidate: %s is not included in pipeline: %s" % (candidate_id, talent_pipeline.id))

        db.session.commit()

        update_candidates_on_cloudsearch(request.oauth_token, candidate_ids)

        activity_data = {
            'name': talent_pipeline.name
        }
        candidates = Candidate.query.with_entities(Candidate.id, Candidate.formatted_name).filter(
            Candidate.id.in_(removed_candidate_ids)).all()

        for candidate_id, formatted_name in candidates:
            activity_data['formattedName'] = formatted_name
            add_activity(user_id=request.user.id, activity_type=Activity.MessageIds.PIPELINE_REMOVE_CANDIDATE,
                         source_table=Candidate.__tablename__, source_id=candidate_id, params=activity_data)

        return '', 204

    @require_all_permissions(Permission.PermissionNames.CAN_GET_CANDIDATES)
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
            raise NotFoundError("Talent pipeline with id {} doesn't exist in database".format(talent_pipeline_id))

        if request.user.role.name != 'TALENT_ADMIN' and talent_pipeline.user.domain_id != request.user.domain_id:
            raise ForbiddenError("Logged-in user and talent_pipeline belong to different domain")

        request_params = dict()
        request_params['fields'] = request.args.get('fields', '')
        request_params['sort_by'] = request.args.get('sort_by', '')
        request_params['limit'] = request.args.get('limit', '')
        request_params['page'] = request.args.get('page', '')

        return get_candidates_of_talent_pipeline(talent_pipeline, request.oauth_token, request_params)


class TalentPipelineMostEngagedCandidates(Resource):
    # Access token decorator
    decorators = [require_oauth()]

    @require_all_permissions(Permission.PermissionNames.CAN_GET_CANDIDATES)
    def get(self, **kwargs):
        """
        GET /talent-pipelines/<id>/candidates/engagement?limit=5  Fetch candidates of a talent-pipeline
        :return A dictionary containing list of most engaged candidates belonging to a talent-pipeline

        :rtype: dict
        """

        talent_pipeline_id = kwargs.get('id')
        limit = request.args.get('limit', 5)

        if not is_number(limit) or int(limit) < 1:
            raise InvalidUsage("Limit should be a positive integer")

        talent_pipeline = TalentPipeline.query.get(talent_pipeline_id)

        if not talent_pipeline:
            raise NotFoundError("Talent pipeline with id {} doesn't exist in database".format(talent_pipeline_id))

        if request.user.role.name != 'TALENT_ADMIN' and talent_pipeline.user.domain_id != request.user.domain_id:
            raise ForbiddenError("Logged-in user and talent_pipeline belong to different domain")

        return {'candidates': top_most_engaged_candidates_of_pipeline(talent_pipeline_id, int(limit))}


class CandidateMostEngagedPipelines(Resource):
    # Access token decorator
    decorators = [require_oauth()]

    @require_all_permissions(Permission.PermissionNames.CAN_GET_CANDIDATES)
    def get(self, **kwargs):
        """
        GET /candidates/<candidate_id>/talent-pipelines?limit=5  Fetch Engagement score of a
        candidate in each pipeline
        :return A dictionary containing list of most engaged candidates belonging to a talent-pipeline

        :rtype: dict
        """

        candidate_id = kwargs.get('id')
        limit = request.args.get('limit', 5)

        if not is_number(limit) or int(limit) < 1:
            raise InvalidUsage("Limit should be a positive integer")

        candidate = Candidate.query.get(candidate_id)

        if not candidate:
            raise NotFoundError(error_message="Candidate with id {} doesn't exist in database".format(candidate_id))

        if request.user.role.name != 'TALENT_ADMIN' and candidate.user.domain_id != request.user.domain_id:
            raise ForbiddenError("Logged-in user and candidate belong to different domain")

        return {'talent_pipelines': top_most_engaged_pipelines_of_candidate(candidate_id, int(limit))}


class TalentPipelineCampaigns(Resource):
    # Access token decorator
    decorators = [require_oauth()]

    @require_all_permissions(Permission.PermissionNames.CAN_GET_CAMPAIGNS)
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
            raise NotFoundError("Talent pipeline with id {} doesn't exist in database".format(talent_pipeline_id))

        if request.user.role.name != 'TALENT_ADMIN' and talent_pipeline.user.domain_id != request.user.domain_id:
            raise ForbiddenError("Logged-in user and talent_pipeline belong to different domain")

        page = request.args.get('page', DEFAULT_PAGE)
        per_page = request.args.get('per_page', 20)

        if not is_number(page) or not is_number(per_page) or int(page) < 1 or int(per_page) < 1:
            raise InvalidUsage("page and per_page should be positive integers")

        page = int(page)
        per_page = int(per_page)

        # Get the email campaigns
        include_fields = request.values['fields'].split(',') if request.values.get('fields') else None
        email_campaigns = talent_pipeline.get_email_campaigns(page=page, per_page=per_page)

        headers = generate_pagination_headers(talent_pipeline.get_email_campaigns_count(), per_page, page)

        response = {
            'page_number': page, 'email_campaigns_per_page': per_page,
            'total_number_of_email_campaigns': talent_pipeline.get_email_campaigns_count(),
            'email_campaigns': [email_campaign.to_dict(include_fields) for email_campaign in email_campaigns]
        }

        return ApiResponse(response=response, headers=headers, status=200)


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
    offset = request.args.get('offset', 0)

    response = get_stats_generic_function(talent_pipeline, 'TalentPipeline', request.user, from_date_string,
                                          to_date_string, interval, False, offset)
    if 'is_update' in request.args:
        return '', 204
    else:
        return jsonify({'talent_pipeline_data': response})


api = TalentApi(talent_pipeline_blueprint)
api.add_resource(TalentPipelineApi, CandidatePoolApi.TALENT_PIPELINE, CandidatePoolApi.TALENT_PIPELINES)
api.add_resource(TalentPipelineSmartListApi, CandidatePoolApi.TALENT_PIPELINE_SMARTLISTS)
api.add_resource(TalentPipelineCandidates, CandidatePoolApi.TALENT_PIPELINE_CANDIDATES)
api.add_resource(TalentPipelineMostEngagedCandidates, CandidatePoolApi.TALENT_PIPELINE_ENGAGED_CANDIDATES)
api.add_resource(CandidateMostEngagedPipelines, CandidatePoolApi.CANDIDATES_ENGAGED_TALENT_PIPELINES)
api.add_resource(TalentPipelineCampaigns, CandidatePoolApi.TALENT_PIPELINE_CAMPAIGNS)

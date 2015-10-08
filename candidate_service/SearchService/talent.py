# -*- coding: utf-8 -*-
import math
import json
import hashlib

from dateutil.parser import parse
import simplejson
import requests
from urlparse import urlparse

import TalentSmartListAPI
from TalentAreasOfInterest import get_or_create_areas_of_interest, get_area_of_interest_id_to_sub_areas_of_interest
from TalentCloudSearch import upload_candidate_documents
from TalentUsers import is_current_user_admin
from TalentCloudSearch import search_candidates
from TalentScheduler import queue_task
from ResumeParsing import parse_filepicker_resumes
from ResumeParsing import ResumesImportCacheManager


@auth.requires_login()
def index():
    response.title = "Search"
    session.forget(response)

    search_form_data = get_search_form_data(auth.user)
    search_form_data['is_current_user_admin'] = is_current_user_admin()

    # key for getting hidden fields is searchHiddenFields
    domain = db.domain(auth.user.domainId)
    domain_settings_dict = get_domain_settings_dict(domain)
    search_form_data['search_hidden_fields'] = get_hidden_fields_from_domain_settings_dict('search', domain_settings_dict)
    search_form_data['layout_mode'] = domain_settings_dict.get('layoutMode', 0)
    search_form_data['allCustomFieldCategories'] = domain_settings_dict.get('searchHiddenFields', '')

    return search_form_data


def get_search_form_data(user):
    custom_fields_with_cats = db(db.custom_field.domainId == user.domainId).select(
        db.custom_field.id,
        db.custom_field.name,
        db.custom_field_category.name,
        left=db.custom_field_category.on(db.custom_field.categoryId == db.custom_field_category.id))

    custom_fields = dict()
    for field in custom_fields_with_cats:
        if field['custom_field_category'].name in custom_fields:
            custom_fields[field['custom_field_category'].name].append(field['custom_field'])
        else:
            custom_fields[field['custom_field_category'].name] = []
            custom_fields[field['custom_field_category'].name].append(field['custom_field'])

    mode = 'search'
    return dict(
        mode=mode,
        custom_fields=custom_fields
    )


@auth.requires_login()
def smartlists():
    redirect(URL('lists'))


@auth.requires_login()
def lists():
    from urllib import urlencode
    from TalentUsers import users_in_domain

    talent_lists = TalentSmartListAPI.get_in_domain(auth.user.domainId, order=True, get_candidate_count=False)

    # If domain is Kaiser Corporate, hide Job Alert smartlists for non-admin users
    if is_kaiser_domain(auth.user.domainId) and not is_current_user_admin(user_id=auth.user_id):
        talent_lists = filter(lambda row: 'Job Alerts' not in row.name, talent_lists)

    users = users_in_domain(auth.user.domainId)

    # Sort by date
    import time

    sorted(talent_lists,
           key=lambda l: time.mktime(l.addedTime.timetuple()))  # TODO make sorted by date & that on frontend work

    for talent_list in talent_lists:
        talent_list['can_edit'] = 1
        if talent_list.searchParams:
            search_params_dict = simplejson.loads(talent_list.searchParams)
            # Remove Nones because urlencode converts them to 'None'
            for key in list(search_params_dict.keys()):
                if not search_params_dict[key]:
                    del search_params_dict[key]
            talent_list['search_params_query_string'] = urlencode(search_params_dict, doseq=True)
    return dict(lists=talent_lists, users=users)


@auth.requires_login()
def view_smartlist():
    smart_list = db.smart_list(request.args[0])
    result_dict = TalentSmartListAPI.get_candidates(smart_list, candidate_ids_only=True, max_candidates=100)
    candidate_ids = result_dict['candidate_ids']
    total_found = result_dict['total_found']
    candidates = db(db.candidate.id.belongs(candidate_ids)).select(
        db.candidate.id,
        db.candidate.firstName,
        db.candidate.lastName,
        db.candidate.middleName)
    return dict(smart_list=smart_list, candidates=candidates, total_found=total_found)


@auth.requires_login()
def export_csv():
    if not request.vars.candidate_ids: return dict(message="Nothing to export.")
    candidate_ids = request.vars['candidate_ids']
    candidate_ids = candidate_ids.split(',')

    queue_task('_export_csv', function_vars=dict(candidate_ids=candidate_ids, user_id=auth.user.id))
    message = "An email will be sent to %s with the export data." % auth.user.email
    return {"message": message}


@auth.requires_login()
def export_csv_with_filters():
    """
    Export talents with filters
    By doing this, it cures having to specify all candidate ids to export and leading to crash, when exporting large number of candidates

    :param  filters             Filters selected.
    :param  selected_ids        IDs of candidates selected.
    :param  all_selected        If TRUE, all candidates are selected, retrieved by given filters
    :param  deselected_ids      IDS of candidates deselected, given all candidates by filters provided are selected,
                                that is, exporting (ALL candidates - DESELECTED candidates)

    :return:
    """
    if request.vars.all_selected:
        # retrieve all candidates by using filters provided
        search_results = search_candidates(auth.user.domainId,
                                           request.vars.filters,
                                           search_limit=0,
                                           candidate_ids_only=True)
        candidate_ids = search_results['candidate_ids']

        # remove deselected candidates
        if request.vars.deselected_ids:
            candidate_ids = list(set(candidate_ids) - set(request.vars.deselected_ids))
    else:
        candidate_ids = request.vars.selected_ids

    if not candidate_ids:
        response.status = 400
        return dict(message="Nothing to export.")

    queue_task('_export_csv', function_vars=dict(candidate_ids=candidate_ids, user_id=auth.user.id))
    return dict(
        message="An email will be sent to %s with the export data." % auth.user.email
    )


@auth.requires_login()
def create_candidate_list():
    """
    Get id's from post
    Serialize and add them to the db
    return URL to list
    """
    candidate_ids = request.vars['candidate_ids[]'] or {}

    candidate_ids = [int(candidate_id) for candidate_id in candidate_ids]
    if not len(candidate_ids):
        # no candidate_ids
        return response.json({'error': 1})
    json_candidate_ids = json.dumps(candidate_ids)

    m = hashlib.md5()
    m.update(json_candidate_ids + str(auth.user.id))

    hash = m.hexdigest()

    candidate_list_id = db.public_candidate_sharing.insert(userId=auth.user.id, candidateIdList=json_candidate_ids,
                                                           hashKey=hash)

    return response.json({'url': URL('talent', 'candidate_list', args=[candidate_list_id, hash], host=True)})


def candidate_list():
    """
    Gather search results description based off candidate id's in candidate_list
    Sort based off either candidate list order (default), overall_rating, or by date
    Group by page number
    Display results
    """

    candidate_list_id = request.args(0)
    hash_key = request.args(1)

    candidate_list_row = db((db.public_candidate_sharing.id == candidate_list_id) & (
        db.public_candidate_sharing.hashKey == hash_key)).select(db.public_candidate_sharing.ALL)
    if not len(candidate_list_row):
        return ''

    index_data = dict(
        owners=[],
        statuses=[],
        sources=[],
        rating_tags=[],
        candidate_list_id=candidate_list_id,
        hash_key=hash_key,
        mode='public'
    )

    return response.render('talent/index.html', index_data)


def get_view_params():
    isWide = request.vars.wide or False  # not wide by default
    isExpanded = False if request.vars.expanded == "0" else True  # expanded by default
    isMobile = request.user_agent().is_mobile or request.vars.mobile
    isBackgroundTransparent = request.vars.transparent == "1"

    return isWide, isExpanded, isMobile, isBackgroundTransparent


@auth.requires_login()
def import_index():
    if DO_BENCHMARKING:
        global BENCHMARKING_END_DELTA, BENCHMARKING_START_DELTA
        BENCHMARKING_END_DELTA = time.time()
        logger.info("BETWEEN END OF MODEL AND START OF import_index: %s", BENCHMARKING_END_DELTA - BENCHMARKING_START_DELTA)
        BENCHMARKING_START_DELTA = BENCHMARKING_END_DELTA

    response.title = "Import"
    current_user = auth.user

    import TalentUsers
    owners = TalentUsers.users_in_domain(auth.user.domainId)
    sources = db(db.candidate_source.domainId == auth.user.domainId).select()
    custom_fields = db(db.custom_field.domainId == auth.user.domainId).select(cache=(cache.ram, 300))

    # Widget url, button and widget code
    widget_page = get_or_create_widget_page(current_user)
    widget_name = widget_page.widgetName
    widget_url = URL("widget", "show", args=[widget_name], host=True, scheme='https')

    # TODO: walmart wants their button in their blue - make the button_code part of widget_page or something so can be different for each domain
    button_code = '''<button %s onclick="var left=screen.width/2 - 250/2; window.open('%s', '', 'left=' + left + ', width=250, height=700, location=no, menubar=no, scrollbars=no, resizable=no, toolbar=no, status=no, copyhistory=no');" class="btn">Join Our Talent Community</button>''' % (
        'style="background-color:rgb(26, 117, 207);background-image:none;text-shadow:none;color:white;"' if widget_page.widgetName == "walmart" else "",
        widget_url
    )
    widget_code = '''<iframe width="300" height="800" frameborder="0" src="%s" ></iframe>''' % widget_url
    session_id = response.cookies.get('session_id_web').value

    # key for getting hidden fields is searchHiddenFields
    domain = TalentUsers.domain_from_id(auth.user.domainId)
    domain_settings_dict = get_domain_settings_dict(domain)
    import_hidden_fields = get_hidden_fields_from_domain_settings_dict('import', domain_settings_dict)

    # code to quick add candidate
    isWide, isExpanded, isMobile, isBackgroundTransparent = get_view_params()
    # Set <select> options
    areas_of_interest = get_or_create_areas_of_interest(current_user.domainId)

    def sort_aoi(row):
        if row.description == 'All' or row.description == 'All Subcategories':
            return 'A'
        else:
            return row.description

    areas_of_interest_sorted = areas_of_interest.sort(sort_aoi)
    area_of_interest_id_to_sub_areas_of_interest = get_area_of_interest_id_to_sub_areas_of_interest(auth.user.domainId)

    global ALL_CITIES_TAG_NAME  # need this for kaiser corp widget
    mode = 'form'
    form_fields = dict()

    if request.vars.quickaddcandidateflag:
        attached_file = request.vars.file
        form_fields = dict()

        # For some reason request.vars.file keeps returning false, so have to do this
        is_attached_file = attached_file.__class__.__name__ == 'FieldStorage'

        widget_candidate_form_fields = dict()
        for input_field in WIDGET_INPUT_FIELDS:
            widget_candidate_form_fields[input_field] = request.vars.get(input_field)

        # Create/update the candidate via attached resume (if any) and form fields
        candidate_id = create_or_update_candidate_from_widget_form_fields(current_user, widget_candidate_form_fields, widget_page,
                                                                          attached_file=attached_file.file if is_attached_file else None,
                                                                          attached_file_ext=ext_from_filename(
                                                                              attached_file.filename) if is_attached_file else None,
                                                                          candidate_id=None)
        response.flash = 'Candidate successfully added'

    # key for getting hidden fields is searchHiddenFields
    layout_mode = domain_settings_dict.get('layoutMode', 0)

    if DO_BENCHMARKING:
        BENCHMARKING_END_DELTA = time.time()
        logger.info("BETWEEN START OF IMPORT_INDEX AND END OF IMPORT_INDEX: %s", BENCHMARKING_END_DELTA - BENCHMARKING_START_DELTA)
        BENCHMARKING_START_DELTA = BENCHMARKING_END_DELTA

    return dict(
        sources=sources,
        owners=owners,
        session_id=session_id,
        button_code=button_code,
        widget_code=widget_code,
        areas_of_interest=areas_of_interest_sorted,
        custom_fields=custom_fields,
        import_hidden_fields=import_hidden_fields,
        is_current_user_admin=is_current_user_admin(),
        isWide=isWide,
        isExpanded=isExpanded,
        isMobile=isMobile,
        isBackgroundTransparent=isBackgroundTransparent,
        user=current_user,
        widget_page=widget_page,
        area_of_interest_id_to_sub_areas_of_interest=area_of_interest_id_to_sub_areas_of_interest,
        mode=mode,
        form_fields=form_fields,
        layout_mode=layout_mode
    )


@auth.requires_login()
def resume_test_parser():
    if not IS_DEV:
        redirect(URL('dashboard', 'index'))
    current_user = auth.user
    return dict(
        user=current_user,
    )


@auth.requires_login()
def parse_resume():
    session.forget(response)
    resume_file = request.vars.resume.file
    filename = request.vars.resume.filename

    user_id = request.vars.owner_id or auth.user.id
    candidate_id = None
    result = dict()

    source = request.vars.source_id
    try:
        area_interest_id = int(request.vars.area_interest_id)
    except:
        area_interest_id = 0

    try:
        source_id = int(source)
    except:
        source_record = db((db.candidate_source.description == source) & (
            db.candidate_source.domainId == auth.user.domainId)).select().first()
        if not source:
            source_id = None
        elif not source_record:
            source_id = db.candidate_source.insert(description=source, domainId=db.user(user_id).domainId)
        else:
            source_id = source_record.id

    if request.vars.get('bulk_parsing_id'):
        bulk_parsing_session_ticket = request.vars.get('bulk_parsing_id')
        from TalentS3 import upload_to_s3
        folder_path = 'Bulkparser/%s/%s/%s' % (user_id, bulk_parsing_session_ticket, filename)
        upload_to_s3(file_content=resume_file.read(), folder_path=folder_path, name=filename, public=False)
    else:
        file_ext = ext_from_filename(filename)
        from ResumeParsing import parse_resume
        result = parse_resume(user_id, source_id=source_id, file_obj=resume_file, filename_str=filename)
        if result == 400:
            raise HTTP(400, 'Duplicate candidate')
        elif result:
            candidate_id = result.get('candidate_id')
        else:
            raise HTTP(500)

    # Mark Get Started action for Add Talent as complete
    set_get_started_action(auth.user, GET_STARTED_ACTIONS['ADD_TALENT'])

    # Add activity & queue update of all smartlists, if candidate id exists
    if candidate_id:
        if area_interest_id:
            db.candidate_area_of_interest.insert(candidateId=candidate_id, areaOfInterestId=area_interest_id)

        from TalentActivityAPI import TalentActivityAPI
        activity_api = TalentActivityAPI()

        candidate = db(db.candidate.id == candidate_id).select().first() or db.candidate(int(candidate_id))
        candidate_name = candidate.name() if candidate else ''
        activity_api.create(auth.user.id, activity_api.CANDIDATE_CREATE_WEB, source_table='candidate',
                            source_id=candidate_id,
                            params=dict(id=candidate_id, sourceProductId=WEB_PRODUCT_ID, formattedName=candidate_name))

        # Upload to CloudSearch
        upload_candidate_documents(candidate_id)

    return response.render('generic.json', dict(result=result))


@auth.requires_login()
def flush_import_resume_cache():
    ResumesImportCacheManager.clear_cache(auth.user_id)
    return {'info': {'message': 'Import resumes process has been finished'}}


@auth.requires_login()
def resume_import_status():
    import_status = ResumesImportCacheManager.get_cache(auth.user_id) or ''
    return dict(
        import_status=import_status
    )


@auth.requires_login()
def parse_filepicker_resume():
    try:
        upload_status = ResumesImportCacheManager.get_cache(auth.user_id)
        if upload_status.get('is_resume_parsing_in_progress'):
            response.status = 400
            return {'error': {'message': 'Another resume import is already in progress.'}}

        filepicker_keys = request.vars.filepicker_keys.split(',')
        source_id = request.vars.source_id
        aoi_id = request.vars.area_of_interest_id or None

        ResumesImportCacheManager.set_cache(auth.user_id,
                                            total_number_of_resumes=len(filepicker_keys),
                                            number_of_parsed_resumes=0,
                                            number_of_successfully_parsed_resumes=0,
                                            failed_resumes_urls=[],
                                            is_resume_parsing_in_progress=True)
        return dict(
            import_stats=parse_filepicker_resumes(auth.user.id, source_id, aoi_id, filepicker_keys)
        )
    except Exception:
        logger.exception("parse_filepicker_resume exception. user_id: %s, request.vars: %s", auth.user_id, request.vars)
        response.status = 400  # TODO change to 500, only 400 for debugging
        return {'error': {'message': 'Internal server error'}}


@auth.requires_login()
def test_parse_filepicker_resume():
    if not IS_DEV:
        redirect(URL('dashboard', 'index'))
    from TalentS3 import get_s3_filepicker_bucket_and_conn
    from StringIO import StringIO
    from ResumeParsing import parse_resume
    key_prefix = request.vars.filepicker_key
    bucket, conn = get_s3_filepicker_bucket_and_conn()
    for key_obj in bucket.list(prefix=key_prefix):
        resume_file = StringIO(key_obj.get_contents_as_string())
        try:
            result_dict = parse_resume(auth.user.id, resume_file, filename_str=key_obj.name, is_test_parser=True)
        except Exception:
            result_dict = dict(error=True)
        pass
    return result_dict


# public version of the results controller
def public_results():
    # page = int(request.vars.page) if request.vars.page else 1
    # page = 1 if page < 1 else page
    #
    # result_format = request.vars.result_format or ''
    #
    # limit = 15
    # offset = (page - 1) * limit
    #
    # rating_filtered_search = False

    result_format = ''

    candidate_list_id = request.vars.candidate_list_id
    hash_key = request.vars.hash_key

    candidate_list_row = db((db.public_candidate_sharing.id == candidate_list_id) & (
        db.public_candidate_sharing.hashKey == hash_key)).select(db.public_candidate_sharing.ALL)
    if not len(candidate_list_row):
        return ''

    candidate_ids = json.loads(candidate_list_row[0].candidateIdList)

    total_found = len(candidate_ids)

    session.candidate_id_results = candidate_ids
    session.forget(response)

    page = request.vars.page or 1
    start_index = ((page - 1) * 15) - 1 if page > 1 else 0
    candidate_ids = candidate_ids[start_index: 15]

    max_pages = int(math.ceil(total_found / 15.0)) or 1

    from TalentCore import get_search_descriptions
    results = dict()
    results['descriptions'] = get_search_descriptions(candidate_ids)
    results['candidate_ids'] = candidate_ids
    results['search_data'] = dict(descriptions=results['descriptions'], facets=dict(), error=dict(), vars=dict(),
                                  mode='public')
    results['total_found'] = total_found
    results['max_pages'] = max_pages
    results['percentage_matches'] = [100] * total_found


    # TODO: much of the following code is also in results(), so should combine them into 1 function
    candidate_ids_only = True if result_format else False
    # get_percentage_match = not candidate_ids_only
    # search_limit = 999999 if result_format else 15

    session.forget(response)

    if result_format == 'candidate_ids':
        return response.json(dict(candidate_ids=results['candidate_ids']))
    else:
        first_three_results = dict(descriptions=results['search_data']['descriptions'][0:3],
                                   mode=results['search_data'].get('mode'),
                                   percentage_matches=results['percentage_matches'][0:3])
        rest_of_results = dict(descriptions=results['search_data']['descriptions'][3:],
                               mode=results['search_data'].get('mode'),
                               percentage_matches=results['percentage_matches'][3:])
        facet_json = json.dumps(results['search_data']['facets'])

        return """
            $('#searchResultList').html(%(first_three_results_html)s);
            $('#searchResultList').append(%(rest_of_results_html)s);
            /* renderFacets('%(facet_json)s'); */

            $('.numCandidates').html('%(total_found)s');
            $('.numCandidatesOnPage').html('%(num_on_page)s');
            $('.numCurrentPage').html('%(page)s');
            $('#pageNum').val(%(page)s)
            $('.numTotalPages').html('%(num_total_pages)s');
            $('.totalResults').show();
            $("#loadingScreen").hide();
            %(show_no_results_if_none_found)s

            syncCurrentPageSelected();

            var is_all_checked = true;

            $('dd.candidatePast, dd.candidateSkills').each(function(){$(this).expander(expanderSettings);});
        """ % dict(
            first_three_results_html=repr(
                response.render('talent/results/first_three_results.html', first_three_results)),
            rest_of_results_html=repr(response.render('talent/results/results.html', rest_of_results)),
            facet_json=facet_json.replace('\\', '\\\\').replace("'", r"\'"),
            total_found=readable_number(results['total_found']),
            num_on_page=readable_number(len(results['descriptions'])),
            page=readable_number(page),
            num_total_pages=readable_number(results['max_pages']),
            show_no_results_if_none_found="" if results['total_found'] else "$('#noResultsFound').show();"
        )

        # candidate_list_id = request.vars.candidate_list_id
        # hash_key = request.vars.hash_key
        #
        # candidate_list_row = db( (db.public_candidate_sharing.id==candidate_list_id) & (db.public_candidate_sharing.hashKey==hash_key) ).select( db.public_candidate_sharing.ALL )
        # if not len(candidate_list_row):
        # return ''
        #
        # candidate_ids = json.loads(candidate_list_row[0].candidateIdList)
        #
        # total_found = len(candidate_ids)
        #
        # session.candidate_id_results = candidate_ids
        # session.forget(response)
        #
        # #sort candidate ids by list order, overall rating, or by created date
        #
        # page = request.vars.page or 1
        # start_index = ((page - 1) * 15) - 1 if page > 1 else 0
        # candidate_ids = candidate_ids[ start_index : 15 ]
        #
        # max_pages = int( math.ceil(total_found / 15.0) ) or 1
        #
        # search = TalentSearch(db, session, cache=cache, solr_url=SOLR_URL)
        # descriptions = search.get_search_descriptions(candidate_ids)
        #
        # search_data = dict(descriptions=descriptions, error='', hash_key=hash_key, mode='public')
        #
        # return """
        # $('#searchResultList').html(%s);
        #     $('html').css( 'cursor', 'auto' );
        #     $('span.numCandidates').html('%s');
        #     $('span.numCandidatesOnPage').html('%s');
        #     $('input.selectCandidate').change(update_selected_candidates_count);
        #     $('.numCurrentPage').html('%s');
        #     $('#pageNum').val(%s);
        #     $('.numTotalPages').html('%s');
        #     $('.numSelected').html(0);
        # """ % ( repr(response.render('talent/results/results.html', search_data)), total_found, len(descriptions), page, page, max_pages )


@auth.requires_login()
def get_candidate_preview_data():
    if not request.vars.id: return dict(emails=[], phones=[], addresses=[], summary="")
    candidate_id = int(request.vars.id)
    candidate_emails = db(db.candidate_email.candidateId == candidate_id).select(db.candidate_email.address,
                                                                                 db.candidate_email.emailLabelId,
                                                                                 db.candidate_email.candidateId).as_list()
    candidate_phones = db(db.candidate_phone.candidateId == candidate_id).select(db.candidate_phone.value,
                                                                                 db.candidate_phone.phoneLabelId,
                                                                                 db.candidate_phone.candidateId).as_list()
    candidate_addresses = db(db.candidate_address.candidateId == candidate_id).select(db.candidate_address.ALL).as_list()
    phone_label_id_to_description = db(db.phone_label.id > 0).select(cache=(cache.ram, 300)).as_dict('id')
    email_label_id_to_description = db(db.email_label.id > 0).select(cache=(cache.ram, 300)).as_dict('id')

    for candidate_phone in candidate_phones:
        candidate_phone['phoneLabel'] = phone_label_id_to_description.get(candidate_phone['phoneLabelId'])[
            'description']
    for candidate_email in candidate_emails:
        candidate_email['emailLabel'] = email_label_id_to_description.get(candidate_email['emailLabelId'])[
            'description']
    for candidate_address in candidate_addresses:
        candidate_address['country'] = country_code_to_name(candidate_address['countryId'])

    # candidate_phones = [row.setdefault('phoneLabel', phone_label_id_to_description.get(row['phoneLabelId'])) for row in candidate_phones]
    # candidate_emails = [row.setdefault('emailLabel', email_label_id_to_description.get(row['emailLabelId'])) for row in candidate_emails]

    return dict(emails=candidate_emails, phones=candidate_phones, addresses=candidate_addresses, summary=db.candidate(candidate_id).summary)


@auth.requires_login()
def results():
    page = int(request.vars.page) if request.vars.page else 1
    page = 1 if page < 1 else page

    result_format = request.vars.result_format or ''

    limit = 15
    offset = (page - 1) * limit

    rating_filtered_search = False

    candidate_ids_only = True if result_format else False
    get_percentage_match = not candidate_ids_only
    search_limit = 10000 if result_format else 15
    search_results = search_candidates(auth.user.domainId, request.vars, search_limit=search_limit,
                                       candidate_ids_only=candidate_ids_only, get_percentage_match=get_percentage_match)
    # logger.debug("results() \n\nrequest.vars: %s \n\nresults:%s\n", request.vars, results)
    session.forget(response)
    if result_format == 'candidate_ids':
        return response.json(dict(candidate_ids=search_results['candidate_ids']))

    if result_format == 'total_found':
        return response.json(dict(total_found=search_results['total_found']))

    else:
        first_three_results = dict(descriptions=search_results['search_data']['descriptions'][0:3],
                                   mode=search_results['search_data'].get('mode'),
                                   percentage_matches=search_results['percentage_matches'][0:3],
                                   max_score=float(search_results['max_score']),
                                   readable_datetime=readable_datetime)
        rest_of_results = dict(descriptions=search_results['search_data']['descriptions'][3:],
                               mode=search_results['search_data'].get('mode'),
                               percentage_matches=search_results['percentage_matches'][3:],
                               max_score=float(search_results['max_score']))
        facet_json = json.dumps(search_results['search_data']['facets'])

        area_of_interest_query = db(db.area_of_interest.domainId == auth.user.domainId).select(db.area_of_interest.id,
                                                                                               db.area_of_interest.description,
                                                                                               db.area_of_interest.parentId)
        custom_fields = get_search_form_data(auth.user)["custom_fields"]

        area_of_interest_objects_list = []
        for row in area_of_interest_query:
            d = {'id': row.id, 'name': row.description, 'parent': row.parentId}
            area_of_interest_objects_list.append(d)
        area_of_interest_all = json.dumps(area_of_interest_objects_list)

        custom_fields_list = dict()
        for row in custom_fields:
            custom_fields_list[row] = [[x.name, x.id] for x in custom_fields[row]]

        custom_fields_json = json.dumps(custom_fields_list)

        return """
            $('#searchResultList').html(%(first_three_results_html)s);
            $('#searchResultList').append(%(rest_of_results_html)s);
            renderFacets('%(facet_json)s', '%(area_of_interest_all)s', '%(custom_fields_list)s');

            $('.numCandidates').html('%(total_found)s');
            $('.numCandidatesOnPage').html('%(num_on_page)s');
            $('.numCurrentPage').html('%(page)s');
            $('#pageNum').val(%(page)s)
            $('.numTotalPages').html('%(num_total_pages)s');
            $('.totalResults').show();
            $("#loadingScreen").hide();
            %(show_no_results_if_none_found)s

            syncCurrentPageSelected();

            var is_all_checked = true;

            $('input.selectCandidate').each(function(){
                if ( ! $(this).is(':checked') ){
                    is_all_checked = false;
                }
            });

            if ( is_all_checked ){
                $('input.selectAll').attr('checked', 'checked');
            } else {
                $('input.selectAll').removeAttr('checked');
            }

            refreshPercentageMatchGraphs();

            $('dd.candidatePast, dd.candidateSkills').each(function(){$(this).expander(expanderSettings);});
        """ % dict(
            first_three_results_html=repr(
                response.render('talent/results/first_three_results.html', first_three_results)),
            rest_of_results_html=repr(response.render('talent/results/results.html', rest_of_results)),
            facet_json=facet_json.replace('\\', '\\\\').replace("'", r"\'"),
            total_found=readable_number(search_results['total_found']),
            num_on_page=readable_number(len(search_results['search_data']['descriptions'])),
            page=readable_number(page),
            num_total_pages=readable_number(search_results['max_pages']),
            show_no_results_if_none_found="" if search_results['total_found'] else "$('#noResultsFound').show();",
            area_of_interest_all=area_of_interest_all.replace('\\', '\\\\').replace("'", r"\'"),
            custom_fields_list=custom_fields_json.replace('\\', '\\\\\\').replace("'", r"\'"),
        )


@auth.requires_login()
def search():
    """
    Returns search results and facet values in json

    :return: json
    """

    candidate_ids_only = False
    get_percentage_match = True
    search_limit = 15
    page = int(request.vars.page) if request.vars.page else 1
    search_results = search_candidates(auth.user.domainId, request.vars, search_limit=search_limit,
                                       candidate_ids_only=candidate_ids_only, get_percentage_match=get_percentage_match)
    session.forget(response)

    area_of_interest_query = db(db.area_of_interest.domainId == auth.user.domainId).select(db.area_of_interest.id,
                                                                                           db.area_of_interest.description,
                                                                                           db.area_of_interest.parentId)
    custom_fields = get_search_form_data(auth.user)["custom_fields"]

    # area_of_interest_objects_list = []
    # for row in area_of_interest_query:
    #     area_of_interest_objects_list.append(dict(
    #         id=row.id,
    #         name=row.description,
    #         parent=row.parentId
    #     ))

    custom_fields_list = dict()
    for row in custom_fields:
        custom_fields_list[row] = [[x.name, x.id] for x in custom_fields[row]]

    return response.json(dict(
        facets=search_results['search_data']['facets'],
        talents=search_results['search_data']['descriptions'],
        total=search_results['total_found'],
        page=page,
        total_pages=search_results['max_pages'],
        mode=search_results['search_data'].get('mode'),
        percentage_matches=search_results['percentage_matches'],
        max_score=float(search_results['max_score']),
        # area_of_interests=area_of_interest_objects_list,
        custom_fields=custom_fields_list
    ))


# @auth.requires_login()
# Required input: args(0) - candidate id
# If a _formname (table name) is provided, does an update (if id is provided), otherwise insert.
# If no _formname is provided, returns the records associated with the given candidate.


def show():
    session.forget(response)

    mode = request.args(1) or ''
    hash_key = request.args(2) or ''
    if mode == 'public' and not hash_key:
        redirect(URL('index'))
    elif mode == 'public':
        candidate_id = int(request.args(0))
        candidate_list_row = db(db.public_candidate_sharing.hashKey == hash_key).select(
            db.public_candidate_sharing.candidateIdList).first()
        if not candidate_list_row:
            redirect(URL('index'))

        candidate_id_list = json.loads(candidate_list_row.candidateIdList)
        if candidate_id not in candidate_id_list:
            redirect(URL('index'))

    elif not auth.is_logged_in():
        redirect(URL('index'))

    candidate = db.candidate(request.args(0)) or db.candidate(request.vars.candidate_id) or redirect(URL('index'))
    response.title = candidate.name()

    # Verify logged-in user is owner or has domain permissions
    current_user = None
    if mode == 'public':
        can_read = True
        can_write = False
    else:
        current_user = db.user(auth.user_id)
        permissions = get_read_write_permissions(current_user, candidate)
        can_read, can_write = permissions['can_read'], permissions['can_write']
        if not can_read:
            redirect(URL('index'))  # if can't even read, return now

    # If updating or inserting a record, make its SQLFORM and perform the update/insert
    # If deleting a record, delete it and return
    if current_user and can_write and request.vars._formname and \
                    request.vars._formname in ("candidate_education_degree_bullet", "candidate_education_degree", "candidate_experience", "candidate_education", "candidate",
                                               "candidate_address", "candidate_skill", "candidate_email", "candidate_phone",
                                               "candidate_text_comment", "candidate_area_of_interest"):

        table_name = request.vars._formname

        if table_name == "candidate_area_of_interest":
            # delete all existing ones
            db(db.candidate_area_of_interest.candidateId == request.vars.id).delete()
            aoi_items = request.vars.areaOfInterestIds
            # Check if there is no area of intrest and the type of areaOfInterestIds from request.vars
            if aoi_items is not None:
                # If there is only one AOI, the type would be a string.So, converting it to a list
                if isinstance(aoi_items, basestring):
                    aoi_items = [aoi_items]
                for aoiItem in aoi_items:
                    db.candidate_area_of_interest.insert(areaOfInterestId=aoiItem, candidateId=request.vars.id)
            # Upload candidate documents in both the cases i.e., "None" and "Not None"
            upload_candidate_documents(candidate.id)
            return response.json(True)
        else:
            record = db[table_name](request.vars.id)  # if record=None, will perform insert instead of update

        # Delete record if necessary
        deletable = table_name not in ("candidate", "candidate_rating")  # candidate_rating is never deleted, only set to 0
        if request.vars.delete_check:
            if deletable and record:
                db(db[table_name].id == record.id).delete()
                return response.json(True)
            else:
                return response.json(False)

        fields = form_fields(table_name, request) if record else None  # If updating, only get inputted fields
        form = SQLFORM(db[table_name], record=record, deletable=deletable, fields=fields)

        # Add activity
        from TalentActivityAPI import TalentActivityAPI
        activity_api = TalentActivityAPI()
        activity_api.create(current_user.id, activity_api.CANDIDATE_UPDATE, source_table='candidate',
                            source_id=candidate.id,
                            params=dict(sourceProductId=WEB_PRODUCT_ID, client_ip=request.client,
                                        formattedName=candidate.name()))

        # TODO: validate foreign ID permissions
        if not record:  # If inserting and not updating form, add in necessary foreign IDs.
            if table_name == 'candidate_education_degree_bullet':
                form.vars.candidateEducationDegreeId = request.vars.candidateEducationDegreeId
            elif table_name == 'candidate_education_degree':
                form.vars.candidateEducationId = request.vars.candidateEducationId
            elif table_name in ('candidate_education', 'candidate_skill'):
                form.vars.candidateId = request.vars.candidateId
            elif table_name == 'candidate_experience':
                form.vars.candidateId = request.vars.candidateId
            elif table_name in ('candidate_email', 'candidate_phone'):
                form.vars.candidateId = request.vars.candidateId
            elif table_name == 'candidate_source':
                form.vars.domainId = request.vars.domainId
            elif table_name == "candidate_area_of_interest":
                form.vars.candidateId = request.vars.candidateId
                form.vars.areaOfInterestId = request.vars.areaOfInterestId

        if table_name == 'candidate':
            if request.vars.firstName or request.vars.lastName:
                form.vars.formattedName = '%s %s' % (request.vars.firstName, request.vars.lastName)

            if request.vars.addedTime:
                form.vars.addedTime = parse(request.vars.addedTime).strftime('%Y-%m-%d %H:%M:%S')

        if table_name == 'candidate_experience':
            form.vars.isCurrent = 1 if form.vars.isCurrent else 0

        if form.process(session=None, formname=table_name).accepted:
            # Upload to CloudSearch
            upload_candidate_documents(candidate.id)

            response.flash = '%s form submitted' % table_name
            return response.json(True)
        elif form.errors:
            logger.error("Errors updating candidate %s: %s", candidate.id, form.errors)
            return response.json(form.errors)

    elif current_user and can_write and request.vars._formname and request.vars._formname == "candidate_custom_field":  # Custom Fields handling
        # Make dictionary of custom field id -> value
        custom_fields = db(db.custom_field.domainId == current_user.domainId).select()
        custom_fields_dict = dict()
        for custom_field in custom_fields:
            if request.vars.get(str(custom_field.id)):
                custom_fields_dict[custom_field.id] = request.vars.get(str(custom_field.id))
        # Exclude rating custom fields - because it is managed in ratings section
        from TalentUsers import get_or_create_rating_custom_fields
        current_owner = db.user(candidate.ownerUserId)
        rating_custom_fields = get_or_create_rating_custom_fields(current_owner.domainId)
        rating_fields_ids = [rating.id for rating in rating_custom_fields]
        # All custom fields of candidate excluding rating custom fields.
        candidate_custom_fields = db(db.candidate_custom_field.candidateId == candidate.id)(~db.candidate_custom_field.customFieldId.belongs(rating_fields_ids)).select()
        add_candidate_custom_fields(
            candidate.id,
            current_candidate_custom_fields=candidate_custom_fields,
            candidate_custom_fields_dict=custom_fields_dict,
            replace=True
        )

        upload_candidate_documents(candidate.id)  # Update cloudsearch

        return response.json(True)

    elif can_write and request.vars._formname and request.vars._formname == "candidate_rating":  # Ratings handling
        rating_dict = {int(id.split('-')[1]): value for id, value in request.vars.iteritems() if id.startswith('ratingTagId')}
        # Add ratings to custom fields.
        from TalentUsers import add_or_update_ratings
        add_or_update_ratings(candidate.id, rating_dict)

        upload_candidate_documents(candidate.id)  # Update cloudsearch
        return response.json(True)

    elif not can_write and request.vars._formname:  # User does not have write permission
        return response.json("Permission denied")

    # Get candidate_address
    candidate_address = db(db.candidate_address.candidateId == candidate.id).select().first()
    # Make new blank candidate_address if it doesn't exist
    if not candidate_address:
        candidate_address_id = db.candidate_address.insert(candidateId=candidate.id, countryId=1)
        candidate_address = db.candidate_address(candidate_address_id)

    # Get candidate_source
    candidate_source_record = db(db.candidate_source.id == candidate.sourceId).select().first()

    # Get candidate emails and phones and their labels
    candidate_emails = db(db.candidate_email.candidateId == candidate.id).select()
    email_labels = db(db.email_label).select()
    if not candidate_emails: candidate_emails = [{'id': '', 'emailLabelId': email_labels.first().id, 'address': ''}]
    candidate_phones = db(db.candidate_phone.candidateId == candidate.id).select()
    phone_labels = db(db.phone_label).select()
    if not candidate_phones: candidate_phones = [{'id': '', 'phoneLabelId': phone_labels.first().id, 'value': ''}]

    # Get all educations
    educations = db(db.candidate_education.candidateId == candidate.id).select()
    # For each education, get all degrees
    for education in educations:
        education['degrees'] = education.candidate_education_degree.select()
        # For each degree, get all degree bullets
        for degree in education['degrees']:
            degree['candidate_education_degree_bullets'] = degree.candidate_education_degree_bullet.select()

    # Sort educations by the degree start date
    educations = educations.sort(
        lambda row: datetime_from_bullshit_row(row['degrees'].first() if row.get('degrees') else None), reverse=True)

    # Get all candidate_experiences and their bullets
    candidate_experiences = db(db.candidate_experience.candidateId == candidate.id).select()
    for candidate_experience in candidate_experiences:
        candidate_experience['candidate_experience_bullets'] = candidate_experience.candidate_experience_bullet.select()

    # Sort experiences
    candidate_experiences = candidate_experiences.sort(datetime_from_bullshit_row, reverse=True)

    # Skills
    candidate_skills = db(db.candidate_skill.candidateId == candidate.id).select(db.candidate_skill.ALL)

    # Assessment
    candidate_text_comments = db(db.candidate_text_comment.candidateId == candidate.id).select()

    # Get next, prev, and search results URL
    prev_candidate_id = None
    next_candidate_id = None
    try:
        if session.candidate_id_results:
            max_index = len(session.candidate_id_results) - 1
            current_pos = session.candidate_id_results.index(candidate.id)
            if current_pos < max_index:
                next_candidate_id = session.candidate_id_results[current_pos + 1]

            if current_pos > 0:
                prev_candidate_id = session.candidate_id_results[current_pos - 1]
    except Exception, e:
        prev_candidate_id = None
        next_candidate_id = None

    # Get all the form data for this domain
    countries = db(db.country).select(cache=(cache.ram, 300))
    statuses = db(db.candidate_status).select(cache=(cache.ram, 300))
    current_owner = db.user(candidate.ownerUserId)
    owners = db(db.user.domainId == current_owner.domainId).select(cache=(cache.ram, 60))  # All users in same domain
    candidate_sources = db(db.candidate_source.domainId == current_owner.domainId).select(cache=(cache.ram, 300))

    areas_of_interest = get_or_create_areas_of_interest(current_owner.domainId, include_child_aois=True)
    candidate_areas_of_interest = db(db.candidate_area_of_interest.candidateId == candidate.id).select()

    # Get custom field data
    from TalentUsers import RATING_CATEGORY_NAME, get_or_create_rating_custom_fields
    custom_field_cats = db(db.custom_field_category.domainId == current_owner.domainId).select(cache=(cache.ram, 0))
    custom_field_categories = [{"id": cat.id, "name": cat.name} for cat in custom_field_cats if cat.name != RATING_CATEGORY_NAME]

    # Rating logic : Remove ratings from custom_fields so that it won't conflict at html. Create new variables for ratings.
    rating_custom_fields = get_or_create_rating_custom_fields(current_owner.domainId)
    rating_category_id = rating_custom_fields.first().categoryId if rating_custom_fields else -1
    custom_fields = db(db.custom_field.domainId == current_owner.domainId)(db.custom_field.categoryId != rating_category_id).select(cache=(cache.ram, 0), orderby=db.custom_field.categoryId)

    # owner_ratings_tags ==> rating related custom_fields.
    owner_rating_tags = db(db.custom_field.domainId == current_owner.domainId)(db.custom_field.categoryId == rating_category_id).select(cache=(cache.ram, 0), orderby=db.custom_field.categoryId)  # custom_fields.find(lambda cf_rating: cf_rating.categoryId== rating_category.id)
    custom_fields_rating_ids = [rating_tag.id for rating_tag in owner_rating_tags]

    candidate_custom_fields = db(db.candidate_custom_field.candidateId == candidate.id).select()
    domain_custom_fields_values = db(db.candidate_custom_field.customFieldId.belongs(db.custom_field.domainId == auth.user.domainId))(~db.candidate_custom_field.customFieldId.belongs(custom_fields_rating_ids)).select(cache=(cache.ram, 0), groupby=db.candidate_custom_field.value)

    # Extract out ratings from candidate_custom_fields
    candidate_custom_rating_fields = candidate_custom_fields.find(lambda candidate_ratings: candidate_ratings.customFieldId in custom_fields_rating_ids)

    source_product_name = None
    if candidate.sourceProductId == WEB_PRODUCT_ID:
        source_product_name = "Web"
    elif candidate.sourceProductId == WIDGET_PRODUCT_ID:
        source_product_name = "Widget"
    elif candidate.sourceProductId == MOBILE_PRODUCT_ID:
        source_product_name = "Mobile"
    elif candidate.sourceProductId == OPENWEB_PRODUCT_ID:
        source_product_name = "Open Web"

    is_current_user_admin_input = is_current_user_admin(current_user.id)

    # get candidate's hidden fields
    domain = db.domain(current_user.domainId)
    domain_settings_dict = get_domain_settings_dict(domain)
    candidate_hidden_fields = get_hidden_fields_from_domain_settings_dict('candidate', domain_settings_dict)

    # get candidate attached extra documents apart from candidate
    candidate_document = db(db.candidate_document.candidateId == candidate.id).select()
    candidate_additional_files = {}
    layout_mode = domain_settings_dict.get('layoutMode', 0)
    for row in candidate_document:
        document = row.filename
        from TalentS3 import get_s3_url

        candidate_additional_files[document] = get_s3_url("CandidateDocuments/%s" % candidate.id,
                                                          document) if document else ''

    show_social_tab = db(db.candidate_social_network.candidateId == candidate.id).count() > 0
    candidate_work_preference = db(db.candidate_work_preference.candidateId == candidate.id).select().first()
    candidate_preferred_location = db(db.candidate_preferred_location.candidateId == candidate.id).select(join=db.country.on(db.candidate_preferred_location.countryId == db.country.id))

    return locals()


@auth.requires_login()
def history_tab():
    from gluon.storage import Storage

    candidate = db.candidate(request.vars.candidate_id)
    logger.info("history_tab: %s start", candidate.id)
    from time import time
    start_time = time()

    # Get all the form data for this domain
    statuses = db(db.candidate_status).select()
    from TalentUsers import users_in_domain
    current_owner = auth.user  # user_from_id(candidate.ownerUserId)  # db(db.user.id == candidate.ownerUserId).select(cache=(cache.ram, 300)).first()
    owners = users_in_domain(auth.user.domainId)
    candidate_sources = db(db.candidate_source.domainId == current_owner.domainId).select()

    # Timeline contains: Candidate creation, Emails sent to him/her (includes bounces), Opens/Clicks done, Date added to smartlist
    timeline = [dict(datetime=candidate.addedTime, table_name='candidate', data_row=None)]

    # Smartlists: Find out which ones contain the candidate
    logger.info("history_tab: %s Smartlists begin, took %s", candidate.id, time() - start_time)
    start_time = time()
    from TalentSmartListAPI import does_smartlist_contain_candidate
    smartlist_rows_in_domain = TalentSmartListAPI.get_in_domain(auth.user.domainId, order=False, get_candidate_count=False)
    logger.info("history_tab: %s Smartlists get_in_domain, took %s", candidate.id, time() - start_time)
    start_time = time()

    # TODO commenting out the multithreaded implementation. we should use message-passing to compute this data & cache in Redis instead, because the below code RE-USES the existing DB connection, which causes errors, because multiple threads will contend over the 1 connection.
    # import threading
    # threads = []
    # smartlists_containing_candidate = []
    # smartlist_rows_lock = threading.RLock()

    # def thread_safe_populate_smartlists_containing_candidate(smart_list, candidate_id, db, cache, logger, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, CLOUDSEARCH_REGION):
    #     current.db = db
    #     current.cache = cache
    #     current.logger = logger
    #     current.AWS_ACCESS_KEY_ID = AWS_ACCESS_KEY_ID
    #     current.AWS_SECRET_ACCESS_KEY = AWS_SECRET_ACCESS_KEY
    #     current.CLOUDSEARCH_REGION = CLOUDSEARCH_REGION
    #     if does_smartlist_contain_candidate(smart_list, candidate_id):
    #         with smartlist_rows_lock:
    #             smartlists_containing_candidate.append(smart_list)
    #
    # for smartlist_row in smartlist_rows_in_domain:
    #     this_thread = threading.Thread(target=thread_safe_populate_smartlists_containing_candidate,
    #                                    kwargs={'smart_list': smartlist_row,
    #                                            'candidate_id': candidate.id,
    #                                            'db': db,
    #                                            'cache': cache,
    #                                            'logger': logger,
    #                                            'AWS_ACCESS_KEY_ID': AWS_ACCESS_KEY_ID,
    #                                            'AWS_SECRET_ACCESS_KEY': AWS_SECRET_ACCESS_KEY,
    #                                            'CLOUDSEARCH_REGION': CLOUDSEARCH_REGION})
    #     this_thread.start()
    #     threads.append(this_thread)
    # for this_thread in threads:
    #     this_thread.join()

    # Serial implementation
    smartlists_containing_candidate = smartlist_rows_in_domain.find(
        lambda smartlist_row: does_smartlist_contain_candidate(smartlist_row, candidate.id))
    logger.info("history_tab: %s Smartlists end, took %s", candidate.id, time() - start_time)
    start_time = time()

    # Campaigns
    # smartlist_ids = [row.id for row in smartlist_rows]
    # email_campaigns = db(
    #     (db.email_campaign.id == db.email_campaign_smart_list.emailCampaignId) &
    #     (db.email_campaign_smart_list.smartListId.belongs(smartlist_ids))
    # ).select(db.email_campaign.ALL, groupby=db.email_campaign.id)
    # del smartlist_ids

    # Dumblist candidates: Add times when candidate was added to a dumblist.
    # TODO Disable for now. This function takes too long already.
    # (We currently don't know when candidates were added to smartlists)
    # smartlist_candidates = db(db.smart_list_candidate.candidateId == candidate.id).select()
    # for smartlist_candidate in smartlist_candidates:
    #     smartlist = smartlist_rows_containing_candidate.find(
    #         lambda row: row.id == smartlist_candidate.smartListId).first()
    #     if smartlist:  # smartlist could be hidden, in which case this is None
    #         timeline.insert(0, dict(datetime=smartlist_candidate.addedTime, table_name='smart_list_candidate',
    #                                 data_row=Storage(smartlist_candidate=smartlist_candidate, smart_list=smartlist)))

    # Campaign sends & campaigns
    logger.info("history_tab: %s Campaign sends & campaigns begin, took %s", candidate.id, time() - start_time)
    start_time = time()
    email_campaign_sends = db(db.email_campaign_send.candidateId == candidate.id).select()
    email_campaign_send_id_to_email_campaign_send = email_campaign_sends.as_dict('id')
    email_campaign_ids = list({email_campaign_send.emailCampaignId for email_campaign_send in email_campaign_sends})
    email_campaigns = db(
        db.email_campaign.id.belongs(email_campaign_ids)
    ).select()
    email_campaign_id_to_email_campaign = email_campaigns.as_dict('id')

    num_bounced = 0
    for email_campaign_send in email_campaign_sends:
        email_campaign = email_campaign_id_to_email_campaign.get(email_campaign_send.emailCampaignId)
        if email_campaign:
            if email_campaign_send.isSesBounce:
                num_bounced += 1
            data = Storage(email_campaign_send=email_campaign_send, email_campaign=email_campaign)
            timeline.insert(0, dict(datetime=email_campaign_send.sentTime, table_name='email_campaign_send',
                                    data_row=data))
        else:
            logger.error("history_tab: No email_campaign found of ID %s", email_campaign_send.emailCampaignId)
    logger.info("history_tab: %s Campaign sends & campaigns ends, took %s", candidate.id, time() - start_time)
    start_time = time()

    # Opens/clicks
    num_opens = 0
    num_clicks = 0
    email_campaign_send_ids = [row.id for row in email_campaign_sends]
    url_conversion_data_rows = db(
        (db.email_campaign_send_url_conversion.emailCampaignSendId.belongs(email_campaign_send_ids)) &
        (db.email_campaign_send_url_conversion.urlConversionId == db.url_conversion.id) &
        (db.url_conversion.hitCount > 0)
    ).select()
    del email_campaign_send_ids

    for url_conversion_data in url_conversion_data_rows:
        if url_conversion_data.email_campaign_send_url_conversion.type == 0:
            num_opens += 1
        else:
            num_clicks += 1
        email_campaign_send = email_campaign_send_id_to_email_campaign_send.get(
            url_conversion_data.email_campaign_send_url_conversion.emailCampaignSendId
        )
        email_campaign = email_campaign_id_to_email_campaign.get(email_campaign_send['emailCampaignId'])
        if email_campaign:
            data = Storage(email_campaign_send=email_campaign_send, email_campaign=email_campaign,
                           url_conversion=url_conversion_data.url_conversion,
                           email_campaign_send_url_conversion=url_conversion_data.email_campaign_send_url_conversion)
            timeline.insert(0,
                            dict(datetime=url_conversion_data.url_conversion.lastHitTime, table_name='url_conversion',
                                 data_row=data))
    logger.info("history_tab: %s Opens/clicks ends, took %s", candidate.id, time() - start_time)
    start_time = time()

    # Figure out when was last contact
    last_contact = None
    if len(email_campaign_sends) and email_campaign_sends[-1].sentTime:
        ago_data = datetime_ago(email_campaign_sends[-1].sentTime)
        last_contact = dict(value=ago_data['value'], metric='%s%s Ago' % (
            ago_data['metric'].capitalize(), '' if ago_data['value'] == 1 else 's'))
    total_interactions = len(email_campaign_sends) + len(url_conversion_data_rows)
    logger.info("history_tab: %s Last contact ends, took %s", candidate.id, time() - start_time)

    timeline = sorted(timeline, key=lambda entry: entry['datetime'] or request.now, reverse=True)
    return dict(
        candidate=candidate,
        statuses=statuses,
        candidate_sources=candidate_sources,
        current_owner=current_owner,
        owners=owners,
        email_campaigns=email_campaigns,
        email_campaign_sends=email_campaign_sends,
        smartlists_containing_candidate=smartlists_containing_candidate,
        total_interactions=total_interactions,
        num_clicks=num_clicks,
        num_opens=num_opens,
        num_bounced=num_bounced,
        last_contact=last_contact,
        timeline=timeline
    )


@auth.requires_login()
def social_tab():
    import operator

    candidate_id = request.vars.get('candidate_id')
    if not candidate_id:
        raise HTTP(400)
    candidate = db(db.candidate.id == candidate_id).select().first()
    if not candidate:
        raise HTTP(400)

    # Verify the candidate belongs to authed user
    import TalentUsers
    candidate_domain_id = TalentUsers.domain_id_from_user_id(candidate.ownerUserId)
    if candidate_domain_id != auth.user.domainId:
        raise HTTP(403, "You don't own candidate %s", candidate_id)

    # Get the social info
    web_profiles, points, github_profile, stackoverflow_profile = {}, [], {}, {}
    dice_social_id = candidate.diceSocialProfileId
    json_response = requests.get("http://api.thesocialcv.com/v3/profile/data.json", params=dict(apiKey=SOCIALCV_API_KEY, profileId=dice_social_id))
    response_dict = json_response.json()

    # thesocialcv returns errors in json object, not http status
    if json_response.status_code == 200 and not response_dict.get('error', 0):
        graph = response_dict.get('graph', {})
        if not graph:
            logger.error("Response from socialCV API did not have graph: %s", response_dict)
        web_profiles = response_dict.get('webProfiles', {})
        if not web_profiles:
            logger.error("Response from socialCV API did not have webProfiles: %s", response_dict)

        # Silly way to check what's the most active social network ...
        # Needed to modified based on human things, because 100 follower on github means much more than 400 connection on linkedin
        points_dict = {}
        for obj in graph:
            points_dict[obj] = [graph[obj][x] for x in graph[obj] if isinstance(graph[obj][x], int)]

        for obj in points_dict.iteritems():
            points_dict[obj[0]] = sum(obj[1])
        points = sorted(points_dict.items(), key=operator.itemgetter(1))
        points.reverse()

        # Find Github user account and get some info
        github_url = web_profiles.get('GitHub', {}).get('url', None)
        github_profile = get_github_profile_data(github_url) if github_url else {}

        # Find StackOverflow user account and get some info
        stackoverflow_url = web_profiles.get('StackOverflow', {}).get('url', None)
        stackoverflow_profile = get_stackoverflow_profile_data(stackoverflow_url) if stackoverflow_url else {}

    return dict(web_profiles=web_profiles, points=points, github_profile=github_profile, stackoverflow_profile=stackoverflow_profile)


@auth.requires_login()
@cache('github-%s' % request.env.HTTP_REFERER, time_expire=60 * 60 * 24 * 7, cache_model=cache.ram)
def get_github_profile_data(url):
    url = urlparse(url).path
    github_response = requests.get('https://api.github.com/users%s/repos' % url)
    if github_response.status_code == 200:
        return github_response.json()
    else:
        return None


@auth.requires_login()
@cache('stackoverflow-%s' % request.env.HTTP_REFERER, time_expire=60 * 60 * 24 * 7, cache_model=cache.ram)
def get_stackoverflow_profile_data(url):
    """

    :rtype : dict[str, T]
    """
    url = urlparse(url).path.split('/')[2]
    user_api_url = "https://api.stackexchange.com/2.2/users/%s?key=%s&site=stackoverflow&order=desc&sort=reputation&filter=!)69SEcsux)oL6JIQImxMZS9XM7u6" % (url, STACKOVERFLOW_API_KEY)
    answers_api_url = "https://api.stackexchange.com/2.2/users/%s/answers?key=%s&page=1&pagesize=5&order=desc&sort=activity&site=stackoverflow&filter=!1zSk*x-JbtL5ldvBPzty)" % (url, STACKOVERFLOW_API_KEY)
    questions_api_url = "https://api.stackexchange.com/2.2/users/%s/questions?key=%s&order=desc&sort=activity&site=stackoverflow&filter=!4(Yr)(WCa35W7X6B2" % (url, STACKOVERFLOW_API_KEY)

    data = dict()
    user_response = requests.get(user_api_url)
    """
    :type: requests.Response
    """
    if user_response.status_code == 200:
        user_response_json = user_response.json()
        first_item = user_response_json['items'][0] if user_response_json['items'] else {}
        data['reputation'] = first_item.get('reputation', 0)
        data['question_count'] = first_item.get('question_count', 0)
        data['answer_count'] = first_item.get('answer_count', 0)

    answers_response = requests.get(answers_api_url)
    answers = dict()
    if answers_response.status_code == 200:
        for obj in answers_response.json().get('items'):
            answers[obj['answer_id']] = {
                'answer_id': obj['answer_id'],
                'score': obj['score'],
                'is_accepted': obj['is_accepted'],
                'tags': obj['tags'],
                'title': obj['title'],
                'link': obj['link']
            }
        data['answers'] = answers

    questions_response = requests.get(questions_api_url)
    questions = dict()
    if questions_response.status_code == 200:
        for obj in questions_response.json().get('items'):
            questions[obj['question_id']] = {
                'title': obj['title'],
                'link': obj['link'],
                'score': obj['score'],
                'tags': obj['tags']
            }
        data['questions'] = questions

    return data


def candidate_doc_upload():
    candidate_id = request.vars.candidateId
    candidate_doc = request.vars.candidateDocument
    file = candidate_doc.file
    file_name = candidate_doc.filename

    from TalentS3 import upload_to_s3

    upload_to_s3(file.read(), folder_path="CandidateDocuments/%s" % candidate_id, name=file_name, public=False)

    db.candidate_document.insert(candidateId=candidate_id, filename=file_name)

    from TalentS3 import get_s3_url

    return '<div class="attach-file"> <input type="checkbox" class="documentCheckbox" value="%s" style="margin:5px" />%s<br></div>' % (
        get_s3_url("CandidateDocuments/%s" % candidate_id, file_name) if file_name else '', file_name)

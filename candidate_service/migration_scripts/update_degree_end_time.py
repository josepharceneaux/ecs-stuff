"""
This script updates candidate-education-degree's end-time from their end-year & end-month values.

Jira ticket: GET-2172
"""
from candidate_service.candidate_app import app
import time
from datetime import datetime
from candidate_service.common.models.db import db
from candidate_service.modules.talent_cloud_search import upload_candidate_documents
from candidate_service.common.models.candidate import Candidate
from candidate_service.common.models.candidate import CandidateEducation
from candidate_service.common.models.candidate import CandidateEducationDegree
from candidate_service.common.models.user import User, Domain


def candidates_with_degrees(domain_ids):
    """
    Function will:
     - Retrieve candidates with missing degree-end-time and available degree-end-year
     - Update degree-end-time's value with degree-end-year & degree-end-month if available
     - Upload updated candidate's docs to Cloud Search
    :type domain_ids: list
    :rtype: list
    """
    # Retrieve candidates with missing degree-end-time and available degree-end-year
    candidates = Candidate.query.join(User, Domain, CandidateEducation, CandidateEducationDegree).filter(
        (Domain.id.in_(domain_ids)) &
        (CandidateEducationDegree.end_year != None) &
        (CandidateEducationDegree.end_time == None)
    )  # type: Candidate

    start = 0
    candidate_degree_count = candidates.count()
    print "number of candidates that must be processed: {}".format(candidate_degree_count)

    affected_candidate_ids = []
    while start < candidate_degree_count:

        for candidate in candidates.slice(start=start, stop=start + 10).all():
            for education in candidate.educations:  # type: CandidateEducation
                for degree in education.degrees:  # type: CandidateEducationDegree

                    end_year = degree.end_year
                    if end_year:
                        print "end_time updating. Candidate-ID: {}\tDegree-ID: {}".format(candidate.id, degree.id)
                        degree.end_time = datetime(year=degree.end_year, month=degree.end_month or 1, day=1)
                        db.session.commit()

                        affected_candidate_ids.append(candidate.id)

        start += 10

    return affected_candidate_ids


if __name__ == '__main__':
    try:
        start_time = time.time()
        customer_and_test_domain_ids = [90, 104, 134, 144, 148, 146, 147, 116, 161,
                                        129, 159, 157, 152, 150, 117, 128, 111]
        candidate_ids = candidates_with_degrees(customer_and_test_domain_ids)
        print "candidates_with_degrees successful.\tTime: {}".format(time.time() - start_time)

        if candidate_ids:
            print "uploading candidate IDs: {}\nCount: {}".format(candidate_ids, len(candidate_ids))
            upload_candidate_documents(candidate_ids)

        print "script completed successfully. Time: {}".format(time.time() - start_time)
    except Exception as e:
        print "Error: {}".format(e.message)

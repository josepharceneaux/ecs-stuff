"""
To run, do:
python modules/cloudsearch_scripts.py --upload-all-candidate-documents gettalent-prod us-east-1
From inside the container.
"""
import argparse

from candidate_service.common.talent_flask import TalentFlask
from candidate_service.common.talent_config_manager import load_gettalent_config, TalentConfigKeys
from talent_cloud_search import define_index_fields, upload_candidate_documents
from candidate_service.common.models.user import User, Domain
from candidate_service.common.models.candidate import Candidate

parser = argparse.ArgumentParser(description='Scripts for various CloudSearch operations.')
parser.add_argument('--define-index-fields', nargs=2,
                    help='Defines index fields in the given CloudSearch domain name and region')
parser.add_argument('--upload-all-candidate-documents', nargs=2,
                    help='Uploads all Candidate documents to the given CloudSearch domain name and region')
args = parser.parse_args()

app = TalentFlask(__name__)
load_gettalent_config(app.config)

if args.define_index_fields:
    domain_name = args.define_index_fields[0]
    app.config[TalentConfigKeys.CS_DOMAIN_KEY] = domain_name
    region_name = args.define_index_fields[1]
    app.config[TalentConfigKeys.CS_REGION_KEY] = region_name
    define_index_fields()

if args.upload_all_candidate_documents:
    domain_name = args.upload_all_candidate_documents[0]
    app.config[TalentConfigKeys.CS_DOMAIN_KEY] = domain_name
    region_name = args.upload_all_candidate_documents[1]
    app.config[TalentConfigKeys.CS_REGION_KEY] = region_name

    def upload_candidate_documents_in_domain(domain_id):
        """
        Upload all the candidates from given domain to cloudsearch
        :param domain_id: Domain id of which all the candidates needs to be uploaded to cloudsearch
        :return: count of total uploaded candidates
        """

        candidates = Candidate.query.with_entities(Candidate.id).join(User).filter(Candidate.user_id == User.id,
                                                                                   User.domain_id == domain_id).all()
        candidate_ids = [candidate.id for candidate in candidates]
        print "Uploading %s candidates of domain id %s" % (len(candidate_ids), domain_id)
        return upload_candidate_documents(candidate_ids, domain_id)

    def upload_all_candidate_documents():
        """
        Upload all the candidates present in system to cloudsearch.
        :return: total number of candidates uploaded
        """
        adds = 0
        domains = Domain.query.with_entities(Domain.id).all()
        for domain in domains:
            print "Uploading all candidates of domain %s" % domain.id
            upload_candidate_documents_in_domain(domain.id)

    upload_all_candidate_documents()
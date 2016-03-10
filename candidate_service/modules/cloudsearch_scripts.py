import argparse

from candidate_service.common.talent_flask import TalentFlask
from candidate_service.common.talent_config_manager import load_gettalent_config, TalentConfigKeys
from talent_cloud_search import define_index_fields, upload_all_candidate_documents

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
    upload_all_candidate_documents()

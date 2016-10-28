#!/usr/bin/env python

"""
Refresh our ATS data from the ATS
"""

import json

from common.models.workday import WorkdayTable
from common.models.ats import ATS, ATSAccount, ATSCandidate, ATSCredential, db
from common.talent_flask import TalentFlask
from common.talent_config_manager import load_gettalent_config
from common.utils.models_utils import add_model_helpers
from app.api.ats_utils import new_ats_candidate, update_ats_candidate, create_ats_object
from ats.workday import Workday


# We're only using Flask as a hook to set up the DB
app = TalentFlask("ATS-Refresh")
load_gettalent_config(app.config) # Config is required for the DB spec
logger = app.config['LOGGER']
add_model_helpers(db.Model)     # Add helpful DB functions
db.init_app(app)
db.app = app
db.create_all()
db.session.commit()

# Go through all ATS accounts and refresh them
account_list = ATSAccount.query.all()
for account in account_list:
    if account.active:
        account_id = account.id

        ats_name, login_url, user_id, credentials = fetch_auth_data(account_id)
        if login_url:
            ats_object = create_ats_object(logger, ats_name, login_url, user_id, credentials)
            ats_object.authenticate()

            # Get all candidate ids (references)
            # TODO: Refactor with code in class ATSCandidateRefreshService
            individual_references = ats_object.fetch_individual_references()
            for ref in individual_references:
                individual = ats_object.fetch_individual(ref)
                data = { 'profile_json' : individual, 'ats_remote_id' : ref }
                present = ATSCandidate.get_by_ats_id(account_id, ref)
                if present:
                    # Update this individual
                    logger.info("Updating ATS information on {}".format(present.id))
                    if present.ats_table_id:
                        data['ats_table_id'] = present.ats_table_id
                    update_ats_candidate(account_id, present.id, data)
                    ats_object.save_individual(json.dumps(data), present.id)
                else:
                    # Create a new individual
                    candidate = new_ats_candidate(account_id, data)
                    individual = ats_object.save_individual(json.dumps(data), candidate.id)
                    data['ats_table_id'] = individual.id
                    update_ats_candidate(account_id, candidate.id, data)

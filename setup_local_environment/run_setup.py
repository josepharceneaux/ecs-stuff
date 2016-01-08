# -*- coding: utf-8 -*-

"""
Script for developers to use to set up their local & remote resources, like DB data and AWS resources.

Prerequisites:
You must have MySQL running locally and a database called talent_local.
"""

from flask import Flask
from common.talent_config_manager import load_gettalent_config, TalentConfigKeys

app = Flask(__name__)
load_gettalent_config(app.config)

from common.models.db import db
db.init_app(app)
db.app = app


with app.app_context():

    from candidate_service.candidate_app import app
    with app.app_context():
        from candidate_service.modules.talent_cloud_search import (define_index_fields, index_documents,
                                                                   make_search_service_public)

        # Create Amazon Cloud Search Domain if It doesn't exist and define index field for Amazon CloudSearch
        define_index_fields()

        # Make Amazon Cloud Search public
        make_search_service_public()

        # Index Amazon Cloud Search
        index_documents()

    # Create Amazon S3 Bucket
    from common.utils.talent_s3 import create_bucket
    create_bucket()

    from common.models.user import Domain

    # Create new Domain
    domain = Domain(name='getTalent', expiration="2050-04-26 00:00:00")
    db.session.add(domain)
    db.session.commit()

    from user_service.user_app import app

    with app.app_context():
        # Create New user
        from user_service.user_app.user_service_utilties import create_user
        create_user(email=app.config[TalentConfigKeys.EMAIL_KEY], domain_id=domain.id, first_name='John',
                    last_name='Doe', expiration=None)

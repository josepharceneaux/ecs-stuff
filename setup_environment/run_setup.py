# -*- coding: -utf-8 -*-

"""
Script for new developers to use to set up their local & remote resources, like DB data and AWS resources.

Prerequisites:
You must have MySQL running locally and a database called talent_local.

Run:
python setup_environment/run_setup.py

"""
from common.talent_flask import TalentFlask
from common.talent_config_manager import load_gettalent_config, TalentConfigKeys

app = TalentFlask(__name__)
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

        # Insert necessary records into static tables
        from user_service.populate_static_tables import (
            create_candidate_status, create_email_clients, create_email_labels, create_frequencies,
            create_cultures, create_phone_labels, create_classification_types, create_products,
            create_rating_tags, create_social_networks
        )
        from user_service.migration_scripts.domain_user_role_updates import (
            add_domain_roles, add_user_group_to_domains, update_users_group_id, add_talent_pool,
            add_talent_pool_group, add_default_talent_pipelines
        )

        add_user_group_to_domains()
        create_user(email=app.config[TalentConfigKeys.EMAIL_KEY], domain_id=domain.id, first_name='John',
                    last_name='Doe', expiration=None)
        create_candidate_status()
        create_email_labels()
        create_email_clients()
        create_frequencies()
        create_cultures()
        create_phone_labels()
        create_classification_types()
        create_products()
        create_rating_tags()
        create_social_networks()
        add_domain_roles()
        update_users_group_id()
        add_talent_pool()
        add_talent_pool_group()
        add_default_talent_pipelines()

print 'Local Environment setup has been completed successfully'


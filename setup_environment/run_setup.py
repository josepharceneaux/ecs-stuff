# -*- coding: utf-8 -*-

"""
Script for new developers to use to set up their local & remote resources, like DB data and AWS resources.

Prerequisites:
You must have MySQL running locally and a database called talent_local.

Run:
python setup_environment/run_setup.py

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

print 'Local Environment setup has been completed successfully'


# Static Tables
from user_service import domain_user_role_updates
from user_service.common.models.candidate import Candidate, CandidateStatus, ClassificationType
from user_service.common.models.misc import Culture
from user_service.common.models.email_marketing import EmailClient

# Populate DomainRole, TalentPool, UserGroup, TalentPoolCandidate, and TalentPoolGroup
execfile(domain_user_role_updates)


def create_candidate_status():
    """ Populates CandidateStatus table """
    statuses = [
        {'description': 'New', 'notes': 'Newly added candidate'},
        {'description': 'Contacted', 'notes': 'Candidate is contacted'},
        {'description': 'Unqualified', 'notes': 'Candidate is unqualified'},
        {'description': 'Qualified', 'notes': 'Candidate is qualified'},
        {'description': 'Prospect', 'notes': 'Candidate is a prospect'},
        {'description': 'Candidate', 'notes': 'Candidate is highly prospective'},
        {'description': 'Hired', 'notes': 'Candidate is hired'},
        {'description': 'Connector', 'notes': None}
    ]
    for status in statuses:
        candidate_status = CandidateStatus(description=status['description'], notes=status['notes'])
        db.session.add(candidate_status)


def create_classification_types():
    """ Populates ClassificationType table """
    classifications = [
        {'code': 'Unspecified', 'description': 'Unspecified', 'notes': 'the degree is not specified'},
        {'code': 'Bachelors', 'description': 'Bachelors degree', 'notes': 'Bachelors degree, e.g. BS., BA., etc.'},
        {'code': 'Associate', 'description': 'Associate degree', 'notes': 'Undergraduate academic two-year degree'},
        {'code': 'Masters', 'description': "Master's degree", 'notes': "Master's degree, e.g. MSc., MA., etc."},
        {'code': 'Doctorate', 'description': "Doctorate degree", 'notes': "Doctorate degree e.g. PhD, EdD., etc."},
        {'code': 'Somehighschoolorequivalent', 'description': "Some high school or equivalent",
         'notes': "A high school drop out or equivalent level"},
        {'code': 'Highschoolorequivalent', 'description': "High school or equivalent",
         'notes': "A high school degree or equivalent"},
        {'code': 'Professional', 'description': "Professional", 'notes': None},
        {'code': 'Certification', 'description': "Certification", 'notes': None},
        {'code': 'Vocational', 'description': "Vocational", 'notes': None},
        {'code': 'Somecollege', 'description': "Some college", 'notes': None},
        {'code': 'Secondary', 'description': "Secondary", 'notes': None},
        {'code': 'GED', 'description': "GED", 'notes': None},
        {'code': 'Somepostgraduate', 'description': "Some postgraduate", 'notes': None}
    ]
    for classification in classifications:
        classification_type = ClassificationType(code=classification['code'],
                                                 description=classification['description'],
                                                 notes=classification['notes'])
        db.session.add(classification_type)


def create_cultures():
    """ Populates Culture table """
    cultures = [
        {'description': 'English', 'code': 'en-us'}
    ]
    for culture in cultures:
        cult = Culture(description=culture['description'], code=culture['code'])
        db.session.add(cult)


def create_email_clients():
    """ Populates EmailClient table """
    clients = [
        {'name': 'Outlook Plugin'}
    ]
    for client in clients:
        email_client = EmailClient(name=client['name'])
        db.session.add(email_client)

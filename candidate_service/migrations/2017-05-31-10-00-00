"""
This script adds description to the candidate_experience table (in preparation of a migration from candidate_experience_bullet)
"""

from candidate_service.candidate_app import app
from candidate_service.common.models.db import db

db.session.execute("ALTER TABLE `candidate_experience` ADD COLUMN `Description` varchar(10000) DEFAULT NULL")

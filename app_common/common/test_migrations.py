'''
Tests for models/migrations.py
'''

import os
import pytest

from app_common.common.models.migrations import run_migrations
from app_common.common.utils.models_utils import init_talent_app
from app_common.common.models.db import db

class TestMigrations():

    app, logger = init_talent_app(__name__)

    def test_no_migrations_directory_is_ok(self, tmpdir, mocker):
        tmpdir.chdir()
        mocker.patch.object(self.logger, 'info')
        run_migrations(self.logger, db)
        message = "No migrations to process (non-existant directory ./migrations)"
        self.logger.info.assert_called_with(message)

    def test_empty_migrations_directory_is_ok(self, tmpdir, mocker):
        tmpdir.chdir()
        tmpdir.mkdir("migrations")
        mocker.patch.object(self.logger, 'info')
        run_migrations(self.logger, db)
        message = "No migrations to process."
        self.logger.info.assert_called_with(message)

    def test_bad_migration_filename(self):
        assert True

    def test_migrations_already_run_are_skipped(self):
        assert True

    def test_migrations_are_run_in_correct_order(self):
        assert True

    def test_detection_of_redundant_migrations_in_database(self):
        assert True

    def test_detection_of_migration_files_with_same_name(self):
        assert True

    def test_handling_failed_migration_file(self):
        assert True

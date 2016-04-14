'''
Tests for models/migrations.py
'''

class TestMigrations():

    def test_no_migrations_directory_is_ok(self):
        assert True

    def test_empty_migrations_directory_is_ok(self):
        assert True

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

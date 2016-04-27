'''
Tests for models/migrations.py
'''

import os
import shutil
import time
import pytest

from app_common.common.error_handling import *
from app_common.common.models.migration import Migration
from app_common.common.models.migrations import DATETIME_FORMAT, MIGRATIONS_DIRECTORY, run_migrations
from app_common.common.utils.models_utils import init_talent_app
from app_common.common.models.db import db

class TestMigrations():

    faux_migration_code = "my_var = 33\n"

    app, logger = init_talent_app(__name__)

    def create_empty_filename(self, pathname):
        '''
        Create empty file.
        :param pathname: Path to file.
        '''

        f = open(pathname, 'a')
        f.close()

    def create_file(self, pathname, contents):
        '''
        Create file with contents.
        :param pathname: Path to file.
        :param contents: Text to put in file.
        '''

        f = open(pathname, 'a')
        f.write(contents)
        f.close()

    def create_directory(self, pathname):
        '''
        Create empty directory.
        :param pathname: Path to directory.
        '''
        f = os.mkdir(pathname, 0755)

    def ensure_migrations_directory(self, temp):
        '''
        Ensure that the migrations directory for testing exists.
        :param dir: A tmpdir object.
        '''

        # Somewhat convoluted because LocalPath.ensure doesn't seem to work.
        temp.chdir()
        migrations_path = temp.join(MIGRATIONS_DIRECTORY)
        if os.path.isdir(migrations_path.__str__()):
            return migrations_path

        return temp.mkdir(MIGRATIONS_DIRECTORY)

    def create_migration_file(self, dir, filename, contents=None):
        '''
        Create a migrations file.
        :param dir: LocalPath object of directory in which to create 'migrations' directory.
        :param filename: Name to give migration file in 'migrations' directory.
        :param contents: Optional contents to insert into file. Use self.faux_migration_code otherwise.
        :return: The name to be entered in the DB migrations table.
        '''

        migrations_dir = self.ensure_migrations_directory(dir)
        migration_name = "{}/migrations/{}".format(os.path.basename(dir.__str__()), filename)
        pathname = "{}/{}".format(migrations_dir.__str__(), filename)
        if contents:
            self.create_file(pathname, contents)
            print "THERE ARE CONTENTS"
        else:
            self.create_file(pathname, self.faux_migration_code)
            print "NO CONTENTS"
        
        return migration_name

    def test_no_migrations_directory_is_ok(self, tmpdir, mocker):
        '''
        :param tmpdir: Temporary directory provided by fixture.
        :param mocker: Mock object provided by fixture
        '''
        tmpdir.chdir()
        mocker.patch.object(self.logger, 'info')
        run_migrations(self.logger, db)
        message = "No migrations to process (non-existant directory ./migrations)"
        self.logger.info.assert_called_with(message)

    def test_empty_migrations_directory_is_ok(self, tmpdir, mocker):
        '''
        :param tmpdir: Temporary directory provided by fixture.
        :param mocker: Mock object provided by fixture
        '''
        self.ensure_migrations_directory(tmpdir)
        mocker.patch.object(self.logger, 'info')
        run_migrations(self.logger, db)
        message = "No migrations to process."
        self.logger.info.assert_called_with(message)

    def test_bad_migration_file_type(self, tmpdir):
        '''
        :param tmpdir: Temporary directory provided by fixture.
        '''
        migrations_dir = self.ensure_migrations_directory(tmpdir)
        migrations_subdir = "{}/im_a_directory".format(migrations_dir.__str__())
        os.mkdir(migrations_subdir, 0755)
        with pytest.raises(UnprocessableEntity):
            run_migrations(self.logger, db)

    def test_bad_migration_filename(self, tmpdir):
        '''
        :param tmpdir: Temporary directory provided by fixture.
        '''
        migrations_dir = self.ensure_migrations_directory(tmpdir)
        bad_filename = "im-a-bad-bad-filename"
        bad_migration_pathname = "{}/{}".format(migrations_dir.__str__(), bad_filename)
        self.create_empty_filename(bad_migration_pathname)
        with pytest.raises(UnprocessableEntity):
            run_migrations(self.logger, db)

    def test_missing_migrations_table_is_created(self, tmpdir):
        '''
        :param tmpdir: Temporary directory provided by fixture.
        '''

        # First, create a valid migration file
        migration_name = self.create_migration_file(tmpdir, time.strftime(DATETIME_FORMAT, time.gmtime()))

        # Now ensure that no migrations table exists
        if Migration.__tablename__ in db.engine.table_names():
            Migration.__table__.drop(db.engine)
            db.session.commit()

        # Run the migration
        run_migrations(self.logger, db)

        # Validate that a migration table exists with our filename
        if Migration.__tablename__ not in db.engine.table_names():
            raise ResourceNotFound
        migrations_found = db.session.query(Migration).filter(Migration.name == migration_name)
        assert migrations_found.one().name == migration_name

    def test_migrations_already_run_are_skipped(self, tmpdir):
        '''
        :param tmpdir: Temporary directory provided by fixture.
        '''

        # Count any existing records
        preexisting_count = db.session.query(Migration).count()

        # Then create and run 2 migrations and validate the new count
        m0 = '2016-04-19-14-13-00'
        m1 = '2016-04-19-14-13-10'
        name0 = self.create_migration_file(tmpdir, m0)
        name1 = self.create_migration_file(tmpdir, m1)
        run_migrations(self.logger, db)
        current_count = db.session.query(Migration).count()
        assert current_count == preexisting_count + 2

        # Now create two more migrations and validate only two more were run
        preexisting_count = current_count
        m2 = '2016-04-19-14-13-20'
        m3 = '2016-04-19-14-13-30'
        name2 = self.create_migration_file(tmpdir, m2)
        name3 = self.create_migration_file(tmpdir, m3)
        run_migrations(self.logger, db)
        current_count = db.session.query(Migration).count()
        assert current_count == preexisting_count + 2

    def test_migrations_are_run_in_correct_order(self, tmpdir):
        '''
        :param tmpdir: Temporary directory provided by fixture.
        '''

        db.session.execute("truncate {}".format(Migration.__tablename__))

        m0 = '2014-04-19-14-13-00'
        m1 = '2014-04-19-14-13-10'
        m2 = '2014-04-19-14-13-20'
        m3 = '2014-04-19-14-13-30'
        name0 = self.create_migration_file(tmpdir, m0)
        name1 = self.create_migration_file(tmpdir, m1)
        name2 = self.create_migration_file(tmpdir, m2)
        name3 = self.create_migration_file(tmpdir, m3)
        run_migrations(self.logger, db)        

        migrations0 = db.session.query(Migration).filter(Migration.name == name0).all()
        if len(migrations0) != 1:
            raise UnprocessableEntity
        migrations1 = db.session.query(Migration).filter(Migration.name == name1).all()
        if len(migrations1) != 1:
            raise UnprocessableEntity
        migrations2 = db.session.query(Migration).filter(Migration.name == name2).all()
        if len(migrations2) != 1:
            raise UnprocessableEntity
        migrations3 = db.session.query(Migration).filter(Migration.name == name3).all()
        if len(migrations3) != 1:
            raise UnprocessableEntity

        assert migrations0[0].run_at_timestamp >= migrations1[0].run_at_timestamp
        assert migrations1[0].run_at_timestamp >= migrations2[0].run_at_timestamp
        assert migrations2[0].run_at_timestamp >= migrations3[0].run_at_timestamp

    def test_handling_failed_migration_file(self, tmpdir):
        '''
        :param tmpdir: Temporary directory provided by fixture.
        '''

        self.create_migration_file(tmpdir, time.strftime(DATETIME_FORMAT, time.gmtime()), 'break me')
        with pytest.raises(UnprocessableEntity):
            run_migrations(self.logger, db)

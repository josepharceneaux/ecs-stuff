from candidate_pool_service.common.tests.conftest import db
from candidate_pool_service.modules.smartlists import save_smartlist


__author__ = 'Joseph Arceneaux'

class TestMigrationForHash(object):

    def test_column_exists(self):
        '''
        '''

        table_name = 'talent_pool'
        column_name = 'description'
        query = 'select * from information_schema.columns where table_name = \'{}\''.format(table_name)
        results = db.session.query(query)

        found = False
        for row in results:
            print row
            if row[3] == column_name:
                found = True

        assert found == True
        # print "DB: {}".format(db)

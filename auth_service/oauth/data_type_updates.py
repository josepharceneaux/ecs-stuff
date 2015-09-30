import os
from sqlalchemy import create_engine


def database_connection():
    # SQL ALCHEMY DB URL
    if os.environ.get('GT_ENVIRONMENT') == 'dev':
        engine = create_engine('mysql://talent_web:s!loc976892@localhost/talent_local')
    elif os.environ.get('GT_ENVIRONMENT') == 'circle':
         # CircleCI provides circle_test as default configured db.
        engine = create_engine('mysql://talent_ci:s!ci976892@circleci.cp1kv0ecwo23.us-west-1.rds.amazonaws.com/talent_ci')
    elif os.environ.get('GT_ENVIRONMENT') == 'qa':
        engine = create_engine('mysql://talent_web:s!web976892@devdb.gettalent.com/talent_staging')
    elif os.environ.get('GT_ENVIRONMENT') == 'prod':
        engine = create_engine(os.environ.get('DB_STRING'))
    else:
        raise Exception("Environment variable GT_ENVIRONMENT not set correctly - could not run app.")

    return engine


def update_table_column_data_type(table_name, data_type_to_change_to):
    print "********** update_table_column_data_type **********"
    engine = database_connection()
    print "database connection: %s" % engine
    return _update_data_type(engine, table_name, data_type_to_change_to)


def _update_data_type(engine, referenced_table_name, data_type_to_change_to):
    """
    :param list_of_column_names:    list of columns that reference parent table, e.g. [userId, user_id, OwnerUserId]
    :param data_type_to_change_to:  e.g. INTEGER, LONGTEXT, etc.
    """
    # Name of database currently in use
    database_name = engine.execute("SELECT DATABASE();").fetchone()[0]
    print "database in use: %s" % database_name

    # Turn on autocommit to prevent deadlock
    engine.execute("SET autocommit=1;")

    # Turn off foreign key checks
    engine.execute("SET FOREIGN_KEY_CHECKS=0;")

    # Get all child tables with FK relationship
    list_of_tables_with_fk_relation = query_tables_with_fk_relation(database_name, engine, referenced_table_name)
    print "list of tables with fk-relations: %s" % list_of_tables_with_fk_relation

    # Drop FKs on child tables
    for dependent_table_tuple in list_of_tables_with_fk_relation:
        query = "ALTER TABLE `%s` DROP FOREIGN KEY `%s`" % (dependent_table_tuple[0], dependent_table_tuple[2])
        print query
        engine.execute(query)

    # Change primary-table`s id-column's data type
    print "ALTER TABLE `%s` MODIFY id %s" % (referenced_table_name, data_type_to_change_to)
    engine.execute("ALTER TABLE `%s` MODIFY id %s" % (referenced_table_name, data_type_to_change_to))

    # Set Primary Key's column to auto-increment
    print "ALTER TABLE %s MODIFY COLUMN id %s auto_increment" % (referenced_table_name, data_type_to_change_to)
    engine.execute("ALTER TABLE %s MODIFY COLUMN id %s auto_increment" % (referenced_table_name, data_type_to_change_to))

    # Generate columns names
    list_of_column_names = generate_column_names(table_name=referenced_table_name)

    # Get all child tables
    dict_of_all_child_tables = query_all_child_tables(engine, database_name, list_of_column_names)
    print "all child tables: %s" % dict_of_all_child_tables

    # Change child table's data type to new data type
    change_data_types(engine, dict_of_all_child_tables, data_type_to_change_to)

    # Create new foreign key for dict_of_child_tables
    for child_table_list in dict_of_all_child_tables.values():
        for child_table in child_table_list:
            query = "ALTER TABLE `%s` ADD CONSTRAINT fk_%s_%s FOREIGN KEY (`%s`) REFERENCES `%s`(id)" % \
                    (child_table[0], referenced_table_name, child_table[0], child_table[1], referenced_table_name)
            print query
            engine.execute(query)

    # Turn foreign key checks back on
    engine.execute("SET FOREIGN_KEY_CHECKS=1;")

    return


def generate_column_names(table_name):
    """
    :param  table_name: referenced_table_name, i.e. Parent table
    :return list of column names associated with Primary-table's id;
            e.g. user.id is referenced as such: ['userId', 'user_id', 'OwnerUserId']
    """
    print "********** generate_column_names **********"
    column_names = ['%s_id' % table_name, '%sid' % table_name]
    if table_name == 'user':
        column_names.append('owneruserid')
    elif table_name == 'area_of_interest':
        column_names.append('areaOfInterestId')
    elif table_name == 'custom_field':
        column_names.append('customFieldId')
    elif table_name == 'candidate_education':
        column_names.append('candidateEducationId')
    elif table_name == 'candidate_education_degree':
        column_names.append('candidateEducationDegreeId')
    elif table_name == 'email_label':
        column_names.append('emailLabelId')
    elif table_name == 'candidate_experience':
        column_names.append('candidateExperienceId')
    elif table_name == 'phone_label':
        column_names.append('phoneLabelId')
    elif table_name == 'rating_tag':
        column_names.append('ratingTagId')
    elif table_name == 'social_network':
        column_names.append('socialNetworkId')
    elif table_name == 'email_client':
        column_names.append('emailClientId')
    elif table_name == 'email_campaign':
        column_names.append('emailCampaignId')
    elif table_name == 'email_campaign_send':
        column_names.append('emailCampaignSendId')
    elif table_name == 'smart_list':
        column_names.append('smartListId')
    elif table_name == 'patent_detail':
        column_names.append('patentDetailId')
    elif table_name == 'candidate_source':
        column_names.append('candidateSourceId')
    elif table_name == 'email_template_folder':
        column_names.append('emailTemplateFolderId')
    elif table_name == 'culture':
        column_names.append('defaultCultureId')
    elif table_name == 'product':
        column_names.append('sourceProductId')

    print "column_names: %s" % column_names
    return column_names


def query_tables_with_fk_relation(database_name, engine, referenced_table_name):
    print "********** query_tables_with_fk_relation **********"
    dependent_tables_list = engine.execute(
        """SELECT TABLE_NAME, COLUMN_NAME, CONSTRAINT_NAME,
           REFERENCED_TABLE_NAME,REFERENCED_COLUMN_NAME FROM
           INFORMATION_SCHEMA.KEY_COLUMN_USAGE WHERE
           TABLE_SCHEMA = %s AND
           REFERENCED_TABLE_NAME = %s""",
        database_name, referenced_table_name).fetchall()

    return dependent_tables_list


def query_all_child_tables(engine, database_name, column_names):
    print "********** query_all_child_tables **********"
    dict_of_child_tables = {}
    for column_name in column_names:
        query = """SELECT TABLE_NAME , COLUMN_NAME , DATA_TYPE FROM
                   INFORMATION_SCHEMA.COLUMNS WHERE COLUMN_NAME = '%s' AND
                   TABLE_SCHEMA = '%s'""" % (column_name, database_name)
        query_result = engine.execute(query).fetchall()
        dict_of_child_tables[column_name] = query_result

    return dict_of_child_tables


def change_data_types(engine, tables, data_type_to_change_to):
    print "********** change_data_types **********"
    for child_table_dicts in tables.values():
        for child_table_list in child_table_dicts:
            query = "ALTER TABLE `%s` MODIFY `%s` %s" % (child_table_list[0], child_table_list[1], data_type_to_change_to)
            print query
            engine.execute(query)


# def select_all_tables_with_id_column():
#     print "********** select_all_tables_with_column_id **********"
#     engine = database_connection()
#     database_name = engine.execute("SELECT DATABASE();").fetchone()[0]
#     list_of_tables = engine.execute(
#         """SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE FROM
#            INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = '%s'
#            AND COLUMN_NAME = 'id';
#         """ % database_name).fetchall()
#     print "list_of_tables: %s" % list_of_tables
#     return list_of_tables


if __name__ == "__main__":

    def run_script():
        # list_of_table_names_to_be_updated = select_all_tables_with_id_column()
        list_of_table_names_to_be_updated = [('user',), ('candidate',)]
        for table_tuple in list_of_table_names_to_be_updated:
            print "#" * 50 + " " + "TABLE: " + str(table_tuple[0].upper()) + " " + "#" * 50
            update_table_column_data_type(table_name=table_tuple[0], data_type_to_change_to='INT')

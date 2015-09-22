import os
from oauth import logger
from sqlalchemy import create_engine


def database_connection():
    # SQL ALCHEMY DB URL
    if os.environ.get('GT_ENVIRONMENT') == 'dev':
        engine = create_engine('mysql://talent_web:s!loc976892@localhost/talent_local')
    elif os.environ.get('GT_ENVIRONMENT') == 'circle':
         # CircleCI provides circle_test as default configured db.
        engine = create_engine('mysql://ubuntu@localhost/circle_test')
    elif os.environ.get('GT_ENVIRONMENT') == 'qa':
        engine = create_engine('mysql://talent_web:s!web976892@devdb.gettalent.com/talent_staging')
    elif os.environ.get('GT_ENVIRONMENT') == 'prod':
        engine = create_engine(os.environ.get('DB_STRING'))
    else:
        raise Exception("Environment variable GT_ENVIRONMENT not set correctly - could not run app.")

    return engine


def update_table_column_data_type(table_name, list_of_column_names, data_type_to_change_to):
    engine = database_connection()
    return _update_data_type(engine=engine, referenced_table_name=table_name,
                             list_of_column_names=list_of_column_names,
                             data_type_to_change_to=data_type_to_change_to)


def _update_data_type(engine, referenced_table_name, list_of_column_names, data_type_to_change_to):
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
    list_of_tables_with_fk_relation = query_tables_with_fk_relation(database_name=database_name,
                                                                    engine=engine,
                                                                    referenced_table_name=referenced_table_name)
    print "list of tables with fk-relations: %s" % list_of_tables_with_fk_relation

    # Drop FKs on child tables
    for dependent_table_tuple in list_of_tables_with_fk_relation:
        engine.execute(
            "ALTER TABLE `%s` DROP FOREIGN KEY `%s`" %
            (dependent_table_tuple[0], dependent_table_tuple[2])
        )
        print "ALTER TABLE `%s` DROP FOREIGN KEY `%s`" % (dependent_table_tuple[0], dependent_table_tuple[2])


    # Change primary-table`s id-column's data type
    engine.execute("ALTER TABLE `%s` MODIFY id %s" % (referenced_table_name, data_type_to_change_to))
    print "ALTER TABLE `%s` MODIFY id %s" % (referenced_table_name, data_type_to_change_to)

    # Set Primary Key's column to auto-increment
    engine.execute("ALTER TABLE %s MODIFY COLUMN id %s auto_increment" % (referenced_table_name, data_type_to_change_to))
    print "ALTER TABLE %s MODIFY COLUMN id %s auto_increment" % (referenced_table_name, data_type_to_change_to)

    # Get all child tables
    dict_of_all_child_tables = query_all_child_tables(engine=engine, database_name=database_name,
                                                      column_names=list_of_column_names)
    print "all child tables: %s" % dict_of_all_child_tables

    # Change child table's data type to new data type
    change_data_types(engine=engine, tables=dict_of_all_child_tables,
                      data_type_to_change_to=data_type_to_change_to)

    # Create new foreign key for dict_of_child_tables
    for child_table_list in dict_of_all_child_tables.values():
        for child_table in child_table_list:
            engine.execute(
                "ALTER TABLE `%s` ADD CONSTRAINT fk_%s_%s FOREIGN KEY (`%s`) REFERENCES `%s`(id)" %
                (child_table[0],
                 referenced_table_name, child_table[0],
                 child_table[1],
                 referenced_table_name)
            )

            print "ALTER TABLE `%s` ADD CONSTRAINT fk_%s_%s FOREIGN KEY (`%s`) REFERENCES `%s`(id)" % \
                  (child_table[0], referenced_table_name, child_table[0], child_table[1], referenced_table_name)

    # Turn foreign key checks back on
    engine.execute("SET FOREIGN_KEY_CHECKS=1;")

    return


def query_tables_with_fk_relation(database_name, engine, referenced_table_name):
    dependent_tables_list = engine.execute(
        """SELECT TABLE_NAME, COLUMN_NAME, CONSTRAINT_NAME,
           REFERENCED_TABLE_NAME,REFERENCED_COLUMN_NAME FROM
           INFORMATION_SCHEMA.KEY_COLUMN_USAGE WHERE
           TABLE_SCHEMA = %s AND
           REFERENCED_TABLE_NAME = %s""",
        database_name, referenced_table_name).fetchall()

    return dependent_tables_list


def query_all_child_tables(engine, database_name, column_names):
    dict_of_child_tables = {}
    for column_name in column_names:
        query = """SELECT TABLE_NAME , COLUMN_NAME , DATA_TYPE FROM
                   INFORMATION_SCHEMA.COLUMNS WHERE COLUMN_NAME = '%s' AND
                   TABLE_SCHEMA = '%s'""" % (column_name, database_name)
        query_result = engine.execute(query).fetchall()
        dict_of_child_tables[column_name] = query_result

    return dict_of_child_tables


def change_data_types(engine, tables, data_type_to_change_to):
    for child_table_dicts in tables.values():
        for child_table_list in child_table_dicts:
            engine.execute(
                "ALTER TABLE `%s` MODIFY `%s` %s" %
                (child_table_list[0], child_table_list[1], data_type_to_change_to)
            )
            print "ALTER TABLE `%s` MODIFY `%s` %s" % (child_table_list[0], child_table_list[1], data_type_to_change_to)

    return


if __name__ == "__main__":
    # update_table_column_data_type(table_name='user',
    #                               list_of_column_names=['userId', 'user_id', 'OwnerUserId'],
    #                               data_type_to_change_to='INTEGER')

    update_table_column_data_type(table_name='candidate',
                                  list_of_column_names=['CandidateId'],
                                  data_type_to_change_to='INTEGER')

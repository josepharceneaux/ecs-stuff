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


def update_user_table_data_type_and_dependent_fks():
    engine = database_connection()

    _update_data_type(referenced_table_name='user', engine=engine)


def _update_data_type(referenced_table_name, engine):
    """ Function will:
            1. Set foreign_key_checks to 0,
            2. Change table's (from params) data type to INTEGER,
            3. Change FK constraints data type to INTEGER,
            4. Set foreign_key_checks to 1

    :param referenced_table_name:   name of the primary table
    :param engine:  local mysql database
    """
    # Turn on autocommit to prevent deadlock
    engine.execute("SET autocommit=1;")

    # Turn off foreign key checks
    engine.execute("SET FOREIGN_KEY_CHECKS=0;")

    # Tables with column that reference user.id
    dependent_tables_list = query_tables_fk_relationship(engine=engine, referenced_table_name=referenced_table_name)

    # Drop FKs on child tables
    for dependent_table_tuple in dependent_tables_list:
        logger.info("ALTER TABLE `%s` DROP FOREIGN KEY `%s`", dependent_table_tuple[0], dependent_table_tuple[2])
        engine.execute(
            "ALTER TABLE `%s` DROP FOREIGN KEY `%s`" % (dependent_table_tuple[0], dependent_table_tuple[2])
        )

    # Update table`s id column`s data type to integer
    logger.info("ALTER TABLE `%s` MODIFY id INTEGER;" % referenced_table_name)
    engine.execute("ALTER TABLE `%s` MODIFY id INTEGER;" % referenced_table_name)

    # Change FK data type to integer for each table in dependent_tables
    for dependent_table_tuple in dependent_tables_list:
        logger.info("ALTER TABLE `%s` MODIFY `%s` INTEGER;" % (dependent_table_tuple[0], dependent_table_tuple[1]))
        engine.execute(
            "ALTER TABLE `%s` MODIFY `%s` INTEGER;" % (dependent_table_tuple[0], dependent_table_tuple[1])
        )

    # Create the foreign key now
    for dependent_table_tuple in dependent_tables_list:
        engine.execute(
            "ALTER TABLE `%s` ADD CONSTRAINT fk_%s_%s FOREIGN KEY (`%s`) REFERENCES `%s`(id)",
            (dependent_table_tuple[0],
             dependent_table_tuple[3], dependent_table_tuple[0],
             dependent_table_tuple[1],
             dependent_table_tuple[3])
        )

    # Turn foreign key checks back on
    engine.execute("SET FOREIGN_KEY_CHECKS=1;")
    return


def query_tables_fk_relationship(engine, referenced_table_name):
    dependent_tables_list = engine.execute(
        "SELECT TABLE_NAME, COLUMN_NAME, CONSTRAINT_NAME, "
        "REFERENCED_TABLE_NAME,REFERENCED_COLUMN_NAME FROM "
        "INFORMATION_SCHEMA.KEY_COLUMN_USAGE WHERE "
        "REFERENCED_TABLE_NAME = %s;", referenced_table_name).fetchall()

    logger.info("Table-columns' data type updated: %s", dependent_tables_list)
    return dependent_tables_list


if __name__ == "__main__":
    update_user_table_data_type_and_dependent_fks()

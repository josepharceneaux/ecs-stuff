__author__ = 'naveen'

from sqlalchemy import create_engine, MetaData, Table

engine = create_engine('mysql://root:root@localhost:3306/talent_local')
conn_db = engine.connect()
metadata = MetaData(bind=engine)


def get_table(table_name=''):
        table = Table(table_name, metadata, autoload=True)
        return table

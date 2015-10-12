from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.orm import sessionmaker
db = SQLAlchemy()
engine = create_engine('mysql://root:root@localhost:3306/talent_local')
conn_db = engine.connect()
metadata = MetaData(bind=engine)
Session = sessionmaker(bind=engine)
session = Session()


def get_table(table_name=''):
        table = Table(table_name, metadata, autoload=True)
        return table

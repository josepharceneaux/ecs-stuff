from sqlalchemy import BIGINT, Column, create_engine, DATETIME, INT, VARCHAR
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

some_engine = create_engine('mysql://root@127.0.0.1/talent_local')
Session = sessionmaker(bind=some_engine)
session = Session()


Base = declarative_base()

class User(Base):
    __tablename__ = 'user'
    Id = Column(BIGINT, primary_key=True)
    email = Column(VARCHAR)

class Token(Base):
    __tablename__ = 'token'
    id = Column(INT, primary_key=True)
    user_id = Column(BIGINT)
    client_id = Column(VARCHAR)
    token_type = Column(VARCHAR)
    access_token = Column(VARCHAR)
    refresh_token = Column(VARCHAR)
    expires = Column(DATETIME)

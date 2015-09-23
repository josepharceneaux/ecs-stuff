"""
A base class from which all models will inherit.
"""
import json

from config import GTSQLAlchemy
from sqlalchemy import exc
from sqlalchemy.orm.exc import NoResultFound


class classproperty(object):
    def __init__(self, getter_func):
        self.getter_func = getter_func

    def __get__(self, instance, owner_class):
        return self.getter_func(owner_class)


class ModelBase(GTSQLAlchemy.BASE):
    """
    This is BaseModel class. This class has following methods:
    1- get
    2- get_by_id
    3- save
    4- delete
    5- update
    6- get_all
    All model classes inherits this base class, so no need to implement above
    mentioned methods in all model classes.
    """
    __abstract__ = True
    query = GTSQLAlchemy.db_session.query_property()

    @classproperty
    def session(cls):
        return GTSQLAlchemy.db_session

    @classmethod
    def get(cls, pk_id):
        """
        This method gets object from database against given id.
        If that object is already in session, this method will not get that
        object from database.
        This function will raise NoResultFound exception if no record found in
        database against given primary key.
        """
        obj = cls.query.get(pk_id)
        if not obj:
            raise NoResultFound
        return obj

    @classmethod
    def get_by_id(cls, pk_id):
        """
        This method gets the latest object from database against given id.
        """
        primary_key = cls.__mapper__.primary_key[0].key
        filter_string = '%s = :value' % primary_key
        return cls.query.filter(filter_string).params(value=pk_id).one()

    @classmethod
    def get_all(cls):
        """Return all records of calling class."""
        return cls.query.all()

    @classmethod
    def save(cls, instance):
        """
        Take object of model class and save that object in database.
        """
        try:
            cls.session.add(instance)
            cls.session.commit()
        except exc.SQLAlchemyError:
            cls.session.rollback()
            raise

    @classmethod
    def delete(cls, pk_id):
        """
        This method gets object against given primary key and delete it from
        database.
        """
        primary_key = cls.__mapper__.primary_key[0].key
        filter_string = '%s = :value' % primary_key
        try:
            rows_deleted = cls.query.filter(filter_string).params(value=pk_id).delete('fetch')
            if rows_deleted:
                cls.session.commit()
        except exc.SQLAlchemyError:
            cls.session.rollback()
            raise
        return rows_deleted

    def update(self, **args):
        """
        1) This methods gets primary key of table of current object.
        2) Make filter string using that primary key.
        3) Finally update current record with given values in args dictionary.

        Note:
        'fetch' string is passed in update function so that it will also update
        object in current session.
        """
        assert args, "No argument given to update method to update this object"
        primary_key = self.__mapper__.primary_key[0].key
        filter_string = '%s = :value' % primary_key # We used this to avoid Sql injection
        try:
            rows_updated = self.query.filter(filter_string).params(value= \
                                   getattr(self, primary_key)).update(args, 'fetch')
            if rows_updated:
                self.session.commit()
        except exc.SQLAlchemyError:
            self.session.rollback()
            raise
        return rows_updated

    def to_json(self):
        """
        Converts SqlAlchemy object to serializable dictionary
        """

        # add your coversions for things like datetime's
        # and what-not that aren't serializable.
        convert = dict(DATETIME=str)

        data = dict()
        for col in self.__class__.__table__.columns:
            value = getattr(self, col.name)
            typ = str(col.type)
            if typ in convert.keys() and value is not None:
                try:
                    data[col.name] = convert[typ](value)
                except Exception as e:
                    data[col.name] = "Error:  Failed to covert using ", str(convert[typ])
            elif value is None:
                data[col.name] = str()
            else:
                data[col.name] = value
        return data

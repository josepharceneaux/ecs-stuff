"""
Author: Zohaib Ijaz, QC-Technologies, <mzohaib.qc@gmail.com>

This modules contains helper methods for Flask-SqlAlchemy models.
On app creation and startup these methods are added in Base Model class from which all
other model classes inherit. But this changes will only effect this app or the app which is calling
"add_model_helpers" function.

    Here is small description of what these methods does:

    * to_json():
        This method converts any models object to json serializable dictionary

    * save():
        This method is adds model instance to session and then commit that change

    * update()
        This method is called upon model instance and updates it.

    * get_by_id(), get()

        These two methods do the same. They return Model instance which matched given id.
        Calling object must be Model class.

    * delete():
        This method deletes Model instance from database given by id.
        Calling object must be Model class.

    * add_model_helpers():
        This function add all the above methods to a class which is passed as argument.
        Mostly this will be db.Model base class in our case but one can add these helper
        methods to a specific Model Class (e.g. Event) by calling this function.

        :Example:

            to add helper methods to db.Model class so that all models classes have that change.

            from model helpers import add_model_helpers

             add_model_helpers(db.Model)

             This will add all these method on db.Model and all its child classes.

"""
# Standard Imports
from types import MethodType

# Third Party
from flask import Flask
from sqlalchemy import inspect
from flask.ext.cors import CORS
from healthcheck import HealthCheck
from flask.ext.sqlalchemy import BaseQuery
from sqlalchemy.orm.dynamic import AppenderQuery

# Application Specific
from ..models.db import db
from ..routes import GTApis, HEALTH_CHECK
from ..redis_cache import redis_store
from ..talent_flask import TalentFlask
from ..utils.talent_ec2 import get_ec2_instance_id
from ..error_handling import register_error_handlers, InvalidUsage
from ..talent_config_manager import (TalentConfigKeys, load_gettalent_config)


def to_json(self, include_fields=None, field_parsers=dict()):
    """
    Converts SqlAlchemy object to serializable dictionary.

    Some data types are not JSON serializable e.g. DATETIME, TIMESTAMP
    so we are making a dictionary where keys are types and values are functions which
    will be used to convert these fields to specific type e.g. str

    field_parsers can be useful in some cases. e.g we want to convert our SqlAlchemy model object
    to JSON serializable dict but we want our datetime object to be converted in
    ISO 8601 format, so we can pass a parser functions like

        >>> from app_common.common.utils.handy_functions import to_utc_str
        >>> parsers = dict(start_datetime=to_utc_str,
        >>>                end_datetime=to_utc_str)
        >>> event.to_json(field_parsers=parsers)

        >>> {
        >>>     ...
        >>>     ...
        >>>     start_datetime: '2016-02-12T12:12:00Z',
        >>>     end_datetime: '2016-03-20T10:10:00Z',
        >>>     ...
        >>> }

     to_json() also handles any naming conventions for db column name and model attribute name.
     e.g. if we have a column name "UserId" in database and "owner_user_id" in model,
     it will handle nicely.

     Serializable dictionary will contain model attribute name as key,
     "owner_user_id" in this case not the db column name "UserId".

     We can get get only required fields by passing names / keys of columns as list or tuple.

        >>> fields = ('first_name', 'last_name', 'status_id', 'added_time')
        >>> candidate = candidate.to_json(include=fields)

    :param self: instance of respective model class
    :type self: db.Model
    :param include_fields: which columns we need to add in JSON data
    :type include_fields: list | tuple
    :param field_parsers: a dictionary with keys as model attributes and values as
     function to parse or convert the field value to specific format
    :type field_parsers: dict
    """
    # add your conversions for things like datetime
    # and timestamp etc. that aren't serializable.
    converters = dict(DATETIME=str, TIMESTAMP=str,
                      DATE=str, TIME=str)

    data = dict()
    cls = self.__class__

    # get column properties
    columns = inspect(cls).column_attrs._data

    if isinstance(include_fields, (list, tuple)):
        allowed_columns = {name: column for name, column in columns.items() if name in include_fields}
        if not allowed_columns:
            raise InvalidUsage('All given column names are invalid: %s' % include_fields)
    else:
        allowed_columns = columns

    # iterate through all columns names, values
    for name, column in allowed_columns.items():
        # get value against this column name
        value = getattr(self, name)

        # e.g. in case of datetime column, column_type will be "DATETIME"
        column_type = str(column.columns[0].type)
        if name in field_parsers and callable(field_parsers[name]):
            # get column type and check if there is any parser or conversion method given
            # for that type. If any, then use parser for conversion
            data[name] = field_parsers[name](value)

        elif column_type in converters and value is not None:
            # try to convert column value by given converter method
            data[name] = converters[column_type](value)

        elif value is None:
            # if value is None, make it empty string
            data[name] = str()
            
        else:
            # it is a normal serializable column value so add to data dictionary as it is.
            data[name] = value
    return data


def save(self):
    """
    This method allows a model instance to save itself in database by calling save
    e.g.
    event = Event(**kwargs)
    Event.save(event)
    :param self: model instance
    :return: same model instance
    """
    # Add instance to db session and then commit that change to save that
    db.session.add(self)
    db.session.commit()
    return self


def update(self, **data):
    """
    This method allows a model instance to update itself in database by calling update
    e.g.
    event = Event.get(event_id)
    event.update(**data)

    :param self: model instance to be updated
    :return: same model instance
    """
    # update this instance by given data
    self.query.filter_by(id=self.id).update(data)
    db.session.commit()
    return self


@classmethod
def create_or_update(cls, conditions, **data):
    """
    This method allows a model instance to create or update itself in database
    :param conditions: a dictionary where keys are column names and values are to match with
     db records in respective table.
     e.g. cls = Event and conditions=dict(social_network_event_id=12345, user_id=2)
     We will search for a record with these conditions like this
        query = cls.query.filter(cls.social_network_event_id == 12345).filter(cls.user_id == 2)

    :param cls: model class, some child class of db.Model
    :param data: data to update model instance
    :return: model instance
    """
    # update this instance by given data
    assert isinstance(conditions, dict) and any(conditions), \
        'first argument should be a valid dictionary'
    query = cls.query
    # apply filter for all given conditions
    for key, value in conditions.iteritems():
        query.filter(getattr(cls, key) == value)

    # get first instance if exists
    instance = query.first()

    try:
        # if there is already a record with given conditions, update it otherwise create a new
        # record
        if instance:
            instance.update(**data)
        else:
            instance = cls(**data)
            cls.save(instance)
    except Exception:
        db.session.rollback()
        raise
    return instance


@classmethod
def get_by_id(cls, _id):
    """
    This method takes an Integer id and returns a model instance of
    that class on which this is invoked.
    e.g. event = Event.get_by_id(2)
    It will return Event class model instance with given id or it will return None if no event found.
    :param cls: model class, some child class of db.Model
    :param _id: id for given instance
    :type _id: int | long
    :return: Model instance
    """
    # get Model instance given by id (primary_key)
    return cls.query.get(_id)


@classmethod
def delete(cls, ref, app=None):
    """
    This method deletes a record from database given by id and the calling Model class.
    :param cls: model class, some child class of db.Model
    :param ref: id for instance | model instance
    :type ref: int | model object
    :param app: flask app, if someone wants to run this method using app_context
    :type app: Flask obj
    :return: Boolean
    :rtype: bool

        :Example:
            You  can delete a record either by primary key or passing the whole model instance.

            # Using primary key
            >>> event_id = 123
            >>> Event.delete(event_id)

            # Using model instance
            >>> event_id = 456
            >>> event = Event.get(event_id)
            >>> if event:
            >>>     Event.delete(event)
    """
    try:
        if isinstance(ref, (int, long)):
            obj = cls.query.get(ref)
        else:
            obj = ref
        db.session.delete(obj)
        db.session.commit()
    except Exception as error:
        db.session.rollback()
        if isinstance(app, Flask):
            with app.app_context():
                app.config[TalentConfigKeys.LOGGER].error(
                    "Couldn't delete record from db. Error is: %s" % error.message)
        return False
    return True


def add_model_helpers(cls):
    """
    This function adds helper methods to Model class which is passed as argument.

        :Example:

            to add helper methods to db.Model class so that all models classes have that change.

            from model helpers import add_model_helpers

             add_model_helpers(db.Model)

             This will add all these method on db.Model and all its child classes.
    :param cls: model class, some child class of db.Model
    """
    cls.session = db.session
    # this method converts model instance to json serializable dictionary
    cls.to_json = MethodType(to_json, None, db.Model)
    # This method saves model instance in database as model object
    cls.save = MethodType(save, None, db.Model)
    # This method updates an existing instance
    cls.update = MethodType(update, None, db.Model)
    # this method returns model instance given by id
    cls.get_by_id = get_by_id
    cls.get = get_by_id
    # This method deletes an instance
    cls.delete = delete

    # Sometimes we have lazy relationship, that is actually just a query (AppenderQuery instance)
    # it contains all methods like filter, filter_by, first, all etc but not paginate, so we are patching `paginate`
    # method from BaseQuery class to AppenderQuery class to get pagination functionality
    # we can now do something like,
    # blasts = campaigns.blasts.paginate(1, 15, False).items
    # or we can call `get_paginated_response` and pass `campaign.blasts` as query.
    AppenderQuery.paginate = BaseQuery.__dict__['paginate']


def init_talent_app(app_name):
    """
    This method initializes the flask app by doing followings:
        1- Create app by using TalentFlask
        2- Loads talent config manager to configure given app
        3- Gets logger
        4- Adds model helpers to the app. This is done to save the effort of adding
            following lines again and again

            db.session.add(instance)
            db.session.commit()

                For example, we just need to do (say)
                    1- to save a new record
                        user_object = User(first_name='Updated Name', last_name='Last Name')
                        User.save(user_object)

                    2- to update a record in database
                        user_obj = User.get_by_id(1)
                        user_obj.update(first_name='Updated Name')

                    3- to delete a record
                        delete by id: User.delete(1)
                        or
                        delete by instance: User.delete(instance)

                    4- to get a record by id
                        User.get(1) or User.get_by_id(1)

                    5- to get json serializable fields of a database record
                        user_obj = User.get_by_id(1)
                        user_json_data  = user_obj.to_json()

        5- Initializes redis store on app instance
        6- Initializes the app by
                db.init_app(flask_app) flask SQLAlchemy builtin
        7- Enable CORS
        8- Registers error handlers for the app
        9- Wraps the flask app and gives a healthcheck URL
    :param app_name: Name of app to be initialize
    :type app_name: str
    :return: Returns the created app and logger
    """
    if not app_name:
        raise InvalidUsage('app_name is required to start an app.')
    flask_app = TalentFlask(app_name)
    load_gettalent_config(flask_app.config)
    # logger init
    logger = flask_app.config[TalentConfigKeys.LOGGER]
    try:
        add_model_helpers(db.Model)
        db.init_app(flask_app)
        db.app = flask_app

        # Initialize Redis Cache
        redis_store.init_app(flask_app)

        # Enable CORS for *.gettalent.com and localhost
        CORS(flask_app, resources=GTApis.CORS_HEADERS)

        # Register error handlers
        logger.info("%s: Registering error handlers" % flask_app.name)
        register_error_handlers(flask_app, logger)

        # wrap the flask app and give a healthcheck URL
        health = HealthCheck(flask_app, HEALTH_CHECK)
        logger.info("Starting %s in %s environment in EC2 instance %s"
                    % (flask_app.import_name, flask_app.config[TalentConfigKeys.ENV_KEY],
                       get_ec2_instance_id()))
        return flask_app, logger
    except Exception as error:
        logger.exception("Couldn't start %s in %s environment because: %s"
                     % (flask_app.name, flask_app.config[TalentConfigKeys.ENV_KEY],
                        error.message))

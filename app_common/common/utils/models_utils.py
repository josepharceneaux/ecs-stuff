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
from flask import current_app
from flask.ext.cors import CORS

# Application Specific
from ..models.db import db
from ..redis_cache import redis_store
from ..error_handling import register_error_handlers
from ..utils.handy_functions import camel_case_to_snake_case
from ..talent_config_manager import (TalentConfigKeys, load_gettalent_config)


def to_json(instance):
    """
    Converts SqlAlchemy object to serializable dictionary

    Some data types are not json serializable e.g. DATETIME, TIMESTAMP
    so we are making a dictionary where keys are types and values are types to which we want to
    convert this data.
    """
    # add your conversions for things like datetime's
    # and what-not that aren't serializable.
    convert = dict(DATETIME=str, TIMESTAMP=str,
                   DATE=str, TIME=str)

    # data dictionary which will contain add data for this instance
    data = dict()
    # iterate through all columns key, values
    for col in instance.__class__.__table__.columns:
        # if name is in camel case convert it to snake case
        name = camel_case_to_snake_case(col.name)
        # get value against this column name
        value = getattr(instance, name)
        # get column type and check if there as any conversion method given for that type.
        # if it is, then use that method or type for data conversion
        typ = str(col.type)
        if typ in convert.keys() and value is not None:
            try:
                # try to convert column value by given converter method
                data[name] = convert[typ](value)
            except:
                data[name] = "Error:  Failed to covert using ", str(convert[typ])
        elif value is None:
            # if value is None, make it empty string
            data[name] = str()
        else:
            # it is a normal serializable column value so add to data dictionary as it is.
            data[name] = value
    return data


def save(instance):
    """
    This method allows a model instance to save itself in database by calling save
    e.g.
    event = Event(**kwargs)
    Event.save(event)
    :return: same model instance
    """
    # Add instance to db session and then commit that change to save that
    db.session.add(instance)
    db.session.commit()
    return instance


def update(instance, **data):
    """
    This method allows a model instance to update itself in database by calling update
    e.g.
    event = Event.get(event_id)
    event.update(**data)
    :return: same model instance
    """
    # update this instance by given data
    instance.query.filter_by(id=instance.id).update(data)
    db.session.commit()
    return instance


@classmethod
def get_by_id(cls, _id):
    """
    This method takes an Integer id and returns a model instance of
    that class on which this is invoked.
    e.g. event = Event.get_by_id(2)
    It will return Event class model instance with given id or it will return None if no event found.
    :param _id: id for given instance
    :type _id: int
    :return: Model instance
    """

    try:
        # get Model instance given by id
        obj = cls.query.get(_id)
    except Exception as error:
        current_app.config[TalentConfigKeys.LOGGER].exception(
            "Couldn't get record from db table %s. Error is: %s" % (cls.__name__, error.message))
        return None
    return obj


@classmethod
def delete(cls, ref):
    """
    This method deletes a record from database given by id and the calling Model class.
    :param ref: id for instance | model instance
    :type ref: int | model object
    :return: Boolean
    :rtype: bool
    """
    try:
        if isinstance(ref, (int, long)):
            obj = cls.query.get(ref)
        else:
            obj = ref
        db.session.delete(obj)
        db.session.commit()
    except Exception as error:
        current_app.config[TalentConfigKeys.LOGGER].error(
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
    :param cls:
    :return:
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


def init_talent_app(flask_app):
    """
    This method initializes the flask app by doing followings:
        1- Loads talent config manager to configure given app
        2- Gets logger
        3- Adds model helpers to the app. This is done to save the effort of adding
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

        4- Initializes redis store on app instance
        5- Initializes the app by
                    db.init_app(flask_app) flask SQLAlchemy builtin
        6- Enable CORS
        7- Registers error handlers for the app
    :return: Returns the app
    """
    load_gettalent_config(flask_app.config)
    # logger init
    logger = flask_app.config[TalentConfigKeys.LOGGER]
    try:
        add_model_helpers(db.Model)
        db.init_app(flask_app)
        db.app = flask_app

        # Initialize Redis Cache
        redis_store.init_app(flask_app)

        # Enable CORS for all origins & endpoints
        CORS(flask_app)
        # Register error handlers
        logger.debug("%s: Registering error handlers." % flask_app.name)
        register_error_handlers(flask_app, logger)
        return flask_app, logger
    except Exception as error:
        logger.exception("Couldn't start %s in %s environment because: %s"
                     % (flask_app.name, flask_app.config[TalentConfigKeys.ENV_KEY],
                        error.message))

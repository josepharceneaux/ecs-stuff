"""
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
__author__ = 'zohaib'
from types import MethodType
from social_network_service.common.models.db import db


def to_json(instance):
    """
    Converts SqlAlchemy object to serializable dictionary

    Some data types are not json serializable e.g. DATETIME, TIMESTAMP
    so we are making a dictionary where keys are types and values are types to which we want to
    convert this data.
    """
    from social_network_service.utilities import camel_case_to_snake_case
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
    event.save()
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
    event = Event(**kwargs)
    event.save()
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
    except:
        return None
    return obj


@classmethod
def delete(cls, ref):
    """
    This method deletes a record from database given by id and the calling Model class.
    :param _id: id for instance
    :type _id: int
    :return: Boolean
    """
    try:
        if isinstance(ref, (int, long)):
            obj = cls.query.get(ref)
        else:
            obj = ref
        db.session.delete(obj)
        db.session.commit()
    except:
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
    # this method converts model instance to json serializeable dictionary
    cls.to_json = MethodType(to_json, None, db.Model)
    # This method saves model instance in database as table row
    cls.save = MethodType(save, None, db.Model)
    # This method updates an existing instance
    cls.update = MethodType(update, None, db.Model)
    # this method returns model instance given by id
    cls.get_by_id = get_by_id
    cls.get = get_by_id
    # This method deletes an instance
    cls.delete = delete
    cls.session = db.session
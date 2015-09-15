__author__ = 'ufarooqi'

from oauth import db
from oauth import logger
from sqlalchemy import create_engine


class User(db.Model):
    __table__ = db.Model.metadata.tables['user']

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return unicode(self.id)


class Domain(db.Model):
    __table__ = db.Model.metadata.tables['domain']

    def get_id(self):
        return unicode(self.id)


class Client(db.Model):
    client_id = db.Column(db.String(40), primary_key=True)
    client_secret = db.Column(db.String(55), nullable=False)

    # Possible values are 'public' or 'confidential'
    @property
    def client_type(self):
        return 'confidential'

    @property
    def allowed_grant_types(self):
        return ['password', 'refresh_token']

    @property
    def default_scopes(self):
        return []

    @property
    def default_redirect_uri(self):
        return ''


class Token(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(
        db.String(40), db.ForeignKey('client.client_id'),
        nullable=False,
    )
    client = db.relationship('Client')

    user_id = db.Column(
        db.BigInteger, db.ForeignKey('user.id')
    )
    user = db.relationship('User')

    # currently only bearer is supported
    token_type = db.Column(db.String(40))

    access_token = db.Column(db.String(255), unique=True)
    refresh_token = db.Column(db.String(255), unique=True)
    expires = db.Column(db.DateTime)
    _scopes = db.Column(db.Text)

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    @property
    def scopes(self):
        if self._scopes:
            return self._scopes.split()
        return []


class DomainRole(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    roleName = db.Column(db.String(255), nullable=False, unique=True)

    domainId = db.Column(
        db.Integer, db.ForeignKey('domain.id')
    )
    domain = db.relationship('Domain')

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    @staticmethod
    def save(domain_id, role_name):
        """ Create a new Role record with the supplied domain_id and role_name.
        :param domain_id: domain id of a role.
        :param role_name: role name of a role.
        """
        role = DomainRole(roleName=role_name, domainId=domain_id)
        db.session.add(role)
        db.session.commit()
        return role.id

    @staticmethod
    def get_by_id(role_id):
        """ Get a role with supplied role_id.
        :param role_id: id of a role.
        """
        return DomainRole.query.get(role_id)

    @staticmethod
    def get_by_name(role_name):
        """ Get a role with supplied role_name.
        :param role_name: Name of a role.
        """
        return DomainRole.query.filter_by(roleName=role_name).first()

    @staticmethod
    def all():
        """ Get all roles_ids in database """
        all_roles = DomainRole.query.all() or []
        return dict(roles=[all_role.id for all_role in all_roles])


class UserScopedRoles(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    userId = db.Column(
        db.BigInteger, db.ForeignKey('user.id'), nullable=False
    )
    roleId = db.Column(
        db.Integer, db.ForeignKey('domain_role.id'), nullable=False
    )
    domainRole = db.relationship('DomainRole')

    @staticmethod
    def add_roles(user_id, roles_list):
        """ Add a role for user
        :param user_id: Id of a user
        :param roles_list: list of roleIds
        """
        for role_id in roles_list:
            if not UserScopedRoles.query.filter(UserScopedRoles.userId == user_id and
                                                UserScopedRoles.roleId == role_id).first():
                if User.query.get(user_id).first() and DomainRole.query.get(role_id).first():
                    user_scoped_role = UserScopedRoles(userId=user_id, roleId=role_id)
                    db.session.add(user_scoped_role)
                else:
                    logger.info("Either user: %s or role_id: %s doesn't exist" % (user_id, role_id))
                    raise Exception("Either user: %s or role_id: %s doesn't exist" % (user_id, role_id))
            else:
                logger.info("Role: %s already exists for user: %s" % (role_id, user_id))
                raise Exception("Role: %s already exists for user: %s" % (role_id, user_id))
        db.session.commit()

    @staticmethod
    def delete_roles(user_id, roles_list):
        """ Delete a role for user
        :param user_id: Id of a user
        :param roles_list: list of roleIds
        """
        for role_id in roles_list:
            user_scoped_role = UserScopedRoles.query.filter(UserScopedRoles.userId == user_id
                                                            and UserScopedRoles.roleId == role_id).first()
            if user_scoped_role:
                db.session.delete(user_scoped_role)
            else:
                logger.info("User %s doesn't have any role %s" % (user_id, role_id))
                raise Exception("User %s doesn't have any role %s" % (user_id, role_id))
        db.session.commit()

    @staticmethod
    def get_all_roles_of_user(user_id):
        """ Get all roles for a user
        :param user_id: Id of a user
        """
        user_scoped_roles = UserScopedRoles.query.filter_by(userId=user_id).all() or []
        return dict(roles=[user_scoped_role.roleId for user_scoped_role in user_scoped_roles])




def update_user_table_data_type_and_dependent_fks():
    # Connect to database
    engine = create_engine("mysql://talent_web:s!loc976892@localhost/talent_local")

    _update_data_type(table='user', engine=engine)
    return


def _update_data_type(table, engine):
    """ Function will:
            1. Set foreign_key_checks to 0,
            2. Change table's (from params) data type to INTEGER,
            3. Change FK constraints data type to INTEGER,
            4. Set foreign_key_checks to 1

    :param table:   name of the primary table
    :param engine:  local mysql database
    """
    # Turn off foreign key checks
    engine.execute("SET FOREIGN_KEY_CHECKS=0;")

    # Tables with column that reference user.id
    dependent_tables_list = query_tables_fk_relationship(engine=engine, table=table)

    # Update user-table's id column's data type to integer
    engine.execute("ALTER TABLE user MODIFY id INTEGER;")

    # Change FK data type to integer for each table in dependent_tables
    for table in dependent_tables_list:
        engine.execute(
            "ALTER TABLE '%s' MODIFY '%s' INTEGER;" % (table[0], table[1])
        )

    # Turn foreign key checks back on
    engine.execute("SET FOREIGN_KEY_CHECKS=1;")
    return


def query_tables_fk_relationship(engine, table):
    dependent_tables_list = engine.execute(
        "select TABLE_NAME, COLUMN_NAME, CONSTRAINT_NAME, "
        "REFERENCED_TABLE_NAME,REFERENCED_COLUMN_NAME from "
        "INFORMATION_SCHEMA.KEY_COLUMN_USAGE where "
        "REFERENCED_TABLE_NAME = '%s';" % table
    )
    logger.info("Number of table-columns' data type updated: %s", len(dependent_tables_list))
    return dependent_tables_list











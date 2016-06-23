"""
File contains json data schema used for validating request-body's json object(s)
"""
source_schema = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "properties": {
        "source": {
            "type": "object",
            "properties": {
                "notes": {
                    "type": ["string", "null"],
                    "maxLength": 5000
                },
                "description": {
                    "type": "string",
                    "maxLength": 1000
                }
            },
            "required": [
                "description"
            ]
        }
    },
    "required": [
        "source"
    ]
}

custom_fields_schema = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "properties": {
        "custom_fields": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {
                        "type": "integer"
                    },
                    "name": {
                        "type": "string"
                    }
                },
                "required": [
                    "name"
                ]
            }
        }
    },
    "required": [
        "custom_fields"
    ]
}

custom_field_schema = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "properties": {
        "custom_field": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string"
                }
            },
            "required": [
                "name"
            ]
        }
    },
    "required": [
        "custom_field"
    ]
}

aoi_schema = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "properties": {
        "areas_of_interest": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "description": {
                        "type": "string",
                        "minLength": 1,
                        "maxLength": 255
                    }
                },
                "required": [
                    "description"
                ]
            }
        }
    },
    "required": [
        "areas_of_interest"
    ]
}

"""
This script adds the simple hash column which is used by the emailed resume to candidate code.
"""

from datetime import datetime
from user_service.common.models.user import User, Permission, Role, db, PermissionsOfRole
from sqlalchemy import text

# Drop domain_role and user_scoped_roles table
db.session.execute(
    text("DROP TABLE `domain_role`;")
)
db.session.execute(
    text("DROP TABLE `user_scoped_roles`;")
)

db.create_all()

permission_names = [key for key in Permission.PermissionNames.__dict__.keys() if not key.startswith('__')]

for permission_name in permission_names:
    db.session.add(Permission(name=permission_name))
db.session.commit()

permissions_not_allowed_for_roles = {
    'USER': [],
    'ADMIN': [],
    'DOMAIN_ADMIN': [],
    'TALENT_ADMIN': []
}

role_names = ['USER', 'ADMIN', 'DOMAIN_ADMIN', 'TALENT_ADMIN']
for role_name in role_names:
    role = Role(role_name)
    db.session.add(role)
    db.session.flush()
    for permission_name in permission_names:
        if permission_name not in permissions_not_allowed_for_roles[role_name]:
            db.session.add(PermissionsOfRole(role_id=role.id, permission_id=Permission.get_by_name(permission_name).id))
    db.session.commit()

    if role_name == 'USER':
        db.session.execute(
            text("ALTER TABLE `user` ADD `role` INT DEFAULT %s CONSTRAINT `fk_user_role` FOREIGN KEY REFERENCES `role` (`id`)" % role.id)
        )

users = User.query.all()

for user in users:
    user.password_reset_time = datetime.utcnow()

db.session.commit()
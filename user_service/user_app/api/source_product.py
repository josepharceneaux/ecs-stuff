"""
File contains endpoints for creating & retrieving Source Product
"""
# Flask specific
from flask import request
from flask_restful import Resource

# Validators
from user_service.common.utils.validators import get_json_data_if_validated

# Models
from user_service.common.models.user import db, Permission
from user_service.common.models.misc import Product

# JSON Schemas
from user_service.modules.json_schema import source_product_schema

# Decorators
from user_service.common.utils.auth_utils import require_oauth, require_all_permissions

# Error handling
from user_service.common.error_handling import InvalidUsage


class SourceProductResource(Resource):
    decorators = [require_oauth()]

    @require_all_permissions(Permission.PermissionNames.CAN_ADD_CANDIDATES)
    def post(self, **kwargs):
        # Validate and obtain json data from request body
        body_dict = get_json_data_if_validated(request, source_product_schema, False)

        # Normalize description & notes
        source_products = body_dict['source_products']

        created_sp_ids = []
        for sp in source_products:
            name = sp['name'].strip()
            notes = (sp.get('notes') or '').strip()

            # In case name is just a whitespace
            if not name:
                raise InvalidUsage("Source product name is required.")

            # Prevent inserting duplicate source product into db
            if name.lower() in {p.name.lower() for p in Product.query.all()}:
                continue

            new_source_product = Product(name=name, notes=notes)
            db.session.add(new_source_product)
            db.session.commit()
            created_sp_ids.append(new_source_product.id)

        return {'source_products': [{'id': sp_id} for sp_id in created_sp_ids]}, 201

    @require_all_permissions(Permission.PermissionNames.CAN_ADD_CANDIDATES)
    def get(self, **kwargs):

        source_product_id = kwargs.get('id')

        # Return a single Source Product if source product ID is provided
        if source_product_id:
            source_product = Product.get(source_product_id)
            if not source_product:
                raise InvalidUsage(error_message="Source Product ID not recognized")

            return {
                'source_product': {
                    'id': source_product.id,
                    'name': source_product.name,
                    'notes': source_product.notes
                }
            }

        # Return all Source Products
        return {
            'source_products': [
                {
                    'id': sp.id,
                    'name': sp.name,
                    'notes': sp.notes,
                } for sp in Product.query.all()]
        }

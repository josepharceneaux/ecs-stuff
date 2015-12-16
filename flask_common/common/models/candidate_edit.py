"""
CandidateEdit table is designed to keep track of changes made to the Candidate's records
"""
from db import db
from sqlalchemy.dialects.mysql import TINYINT
import datetime


class CandidateEdit(db.Model):
    __tablename__ = 'candidate_edit'
    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.Integer)  # ID of the candidate being updated
    field_id = db.Column(db.Integer)  # Hardcoded constants associated with Candidate's fie ld
    user_id = db.Column(db.Integer)  # ID of the user updating the Candidate, NULL if OpenWeb is updating
    is_custom_field = db.Column(db.Boolean, default=False)  # If True, field_id must = custom_field.id
    old_value = db.Column(db.String(50))  # Value of the field before update
    new_value = db.Column(db.String(50))  # Value of the field after update
    edit_type = db.Column(TINYINT, default=None)  # 1 for OpenWeb, 2 for Automatic ClearBit, Null otherwise
    edit_datetime = db.Column(db.TIMESTAMP, default=datetime.datetime.now())  # Timestamp of when edit occurred

    def __repr__(self):
        return "<CandidateEdit (id = %r)" % self.id

    field_dict = {
        'candidate': {
            'first_name': 1,
            'middle_name': 2,
            'last_name': 3,
            'formatted_name': 4,
            'objective': 5,
            'summary': 6,
            'total_months_experience': 7,
            'culture_id': 8
        },
        'candidate_address': {
            'address_line_1': 9,
            'address_line_2': 10,
            'city': 11,
            'state': 12,
            'country_id': 13,
            'zip_code': 14,
            'po_box': 15,
            'is_default': 16
        },
        'candidate_area_of_interest': {
            'area_of_interest_id': 17,
            'additional_notes': 18
        },
        'candidate_custom_field': {
            'value': 19,
            'custom_field_id': 20
        },
        'candidate_education': {
            'school_name': 21,
            'school_type': 22,
            'city': 23,
            'state': 24,
            'country_id': 25,
            'is_current': 26
        },
        'candidate_education_degree': {
            'degree_type': 27,
            'degree_title': 28,
            'start_year': 29,
            'start_month': 30,
            'end_year': 31,
            'end_month': 32,
            'gpa_num': 33,
            'gpa_denom': 34,
            'classification_type_id': 35,
            'start_time': 36,
            'end_time': 37
        },
        'candidate_education_degree_bullet': {
            'concentration_type': 38,
            'comments': 39
        },
        'candidate_experience': {
            'organization': 40,
            'position': 41,
            'city': 42,
            'state': 43,
            'end_month': 44,
            'end_year': 45,
            'start_month': 46,
            'start_year': 47,
            'country_id': 48,
            'is_current': 49
        },
        'candidate_experience_bullet': {
            'description': 50
        },
        'candidate_work_preference': {
            'relocate': 51,
            'authorization': 52,
            'telecommute': 53,
            'travel_percentage': 54,
            'hourly_rate': 55,
            'salary': 56,
            'tax_terms': 57,
            'security_clearance': 58,
            'third_party': 59
        },
        'candidate_email': {
            'email_label_id': 60,
            'address': 61,
            'is_default': 62
        },
    }

    @classmethod
    def get_by_candidate_id(cls, candidate_id):
        return cls.query.filter_by(candidate_id=candidate_id).all()

    @classmethod
    def get_field_id(cls, table_name, field_name):
        for t_name in cls.field_dict.keys():
            if t_name == table_name:
                for column_name in cls.field_dict[t_name].keys():
                    if column_name == field_name:
                        return cls.field_dict[t_name][column_name]

    @classmethod
    def get_table_and_field_names_from_id(cls, field_id):
        for table_name in cls.field_dict.keys():
            for column_name in cls.field_dict[table_name].keys():
                if cls.field_dict[table_name][column_name] == field_id:
                    return table_name, column_name


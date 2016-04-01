"""
CandidateEdit table is designed to keep track of changes made to the Candidate's records
"""
from db import db
from sqlalchemy.dialects.mysql import TINYINT
import datetime


class CandidateEdit(db.Model):
    __tablename__ = 'candidate_edit'
    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.BIGINT, db.ForeignKey('candidate.Id'))
    field_id = db.Column(db.Integer)  # Hardcoded constants associated with Candidate's fie ld
    user_id = db.Column(db.Integer)  # ID of the user updating the Candidate, NULL if OpenWeb is updating
    is_custom_field = db.Column(db.Boolean, default=False)  # If True, field_id must = custom_field.id
    old_value = db.Column(db.String(255))  # Value of the field before update
    new_value = db.Column(db.String(255))  # Value of the field after update
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
            'culture_id': 8,
            'filename': 9,
            'is_web_hidden': 10
        },
        'candidate_address': {
            'address_line_1': 101,
            'address_line_2': 102,
            'city': 103,
            'state': 104,
            'country_id': 105,
            'zip_code': 106,
            'po_box': 107,
            'is_default': 108
        },
        'candidate_area_of_interest': {
            'area_of_interest_id': 201,
            'additional_notes': 202
        },
        'candidate_custom_field': {
            'value': 301,
            'custom_field_id': 302
        },
        'candidate_education': {
            'school_name': 401,
            'school_type': 402,
            'city': 403,
            'state': 404,
            'country_id': 405,
            'is_current': 406
        },
        'candidate_education_degree': {
            'degree_type': 501,
            'degree_title': 502,
            'start_year': 503,
            'start_month': 504,
            'end_year': 505,
            'end_month': 506,
            'gpa_num': 507,
            'gpa_denom': 508,
            'classification_type_id': 509,
            'start_time': 510,
            'end_time': 511
        },
        'candidate_education_degree_bullet': {
            'concentration_type': 601,
            'comments': 602
        },
        'candidate_experience': {
            'organization': 701,
            'position': 702,
            'city': 703,
            'state': 704,
            'end_month': 705,
            'end_year': 706,
            'start_month': 707,
            'start_year': 708,
            'country_id': 709,
            'is_current': 710
        },
        'candidate_experience_bullet': {
            'description': 801
        },
        'candidate_work_preference': {
            'relocate': 901,
            'authorization': 902,
            'telecommute': 903,
            'travel_percentage': 904,
            'hourly_rate': 905,
            'salary': 906,
            'tax_terms': 907,
            'security_clearance': 908,
            'third_party': 909
        },
        'candidate_email': {
            'email_label_id': 1001,
            'address': 1002,
            'is_default': 1003
        },
        'candidate_phone': {
            'phone_label_id': 1101,
            'value': 1102,
            'extension': 1103,
            'is_default': 1104
        },
        'candidate_military_service': {
            'country_id': 1201,
            'service_status': 1202,
            'highest_rank': 1203,
            'highest_grade': 1204,
            'branch': 1205,
            'comments': 1206,
            'from_date': 1207,
            'to_date': 1208
        },
        'candidate_preferred_location': {
            'address': 1301,
            'city': 1302,
            'state': 1303,
            'region': 1304,
            'zip_code': 1305,
            'country_id': 1306
        },
        'candidate_skill': {
            'description': 1401,
            'total_months': 1402,
            'last_used': 1403
        },
        'candidate_social_network': {
            'social_network_id': 1501,
            'social_profile_url': 1502,
            'updated_time': 1503
        },
        'candidate_photo': {
            'image_url': 1601,
            'is_default': 1602
        },
        'candidate_language': {
            'iso639_language': 1701,
            'read': 1702,
            'write': 1703,
            'speak': 1704
        }
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


class CandidateView(db.Model):
    __tablename__ = 'candidate_view'
    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.BIGINT, db.ForeignKey('candidate.Id'))
    user_id = db.Column(db.BIGINT, db.ForeignKey('user.Id'))
    view_type = db.Column(TINYINT)
    view_datetime = db.Column(db.DateTime)

    def __repr__(self):
        return "<CandidateView (candidate_id = %r)>" % self.candidate_id

    @classmethod
    def get_by_id(cls, _id):
        """
        :type _id:  int|long
        :rtype:  CandidateView
        """
        return cls.query.filter_by(id=_id).first()

    @classmethod
    def get_all(cls, candidate_id):
        """
        :type candidate_id:  int|long
        :rtype:  list[CandidateView]
        """
        return cls.query.filter_by(candidate_id=candidate_id).all()

    @classmethod
    def get_by_user_and_candidate(cls, user_id, candidate_id):
        """
        :type user_id:  int|long
        :type candidate_id:  int|long
        :rtype:  list[CandidateView]
        """
        return cls.query.filter_by(user_id=user_id, candidate_id=candidate_id).all()
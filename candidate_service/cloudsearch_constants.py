__author__ = 'jitesh'

RETURN_FIELDS_AND_CORRESPONDING_VALUES_IN_CLOUDSEARCH = {"score": "_score",
                                                         "all_fields": "_all_fields,_score",
                                                         "count_only": "_no_fields,_score",
                                                         # return enabled fields in cloudsearch
                                                         "id": "id",
                                                         "added_time": "added_time",
                                                         "email": "email",
                                                         "first_name": "first_name",
                                                         "last_name": "last_name",
                                                         "objective": "objective",
                                                         "organization": "organization",
                                                         "position": "position",
                                                         "source_id": "source_id",
                                                         "source_product_id": "source_product_id",
                                                         "status_id": "status_id",
                                                         "user_id": "user_id"}

SORTING_FIELDS_AND_CORRESPONDING_VALUES_IN_CLOUDSEARCH = {"match": ("_score", "desc"),
                                                          "~match": ("_score", "asc"),
                                                          "recent": ("added_time", "desc"),
                                                          "~recent": ("added_time", "asc"),
                                                          "proximity": ("distance", "asc"),
                                                          "~proximity": ("distance", "desc")}

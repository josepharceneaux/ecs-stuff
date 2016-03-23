import pycountry as pc


def get_country_name(country_code=None):
    """
    :param country_code:  ISO 3166 country codes
    :return:  Country's name
    """
    if not country_code:
        return 'United States'

    try:
        country = pc.countries.get(alpha2=country_code.upper())
        country_name = country.name
    except KeyError:
        return {'error': 'Country code not recognized: {}'.format(country_code)}

    return country_name


def get_language(language_code=None):
    """
    :param language_code:  ISO 639 language codes
    :return:  language's name
    """
    if not language_code:
        return 'English'

    try:
        language = pc.languages.get(iso639_1_code=language_code.lower())
        language_name = language.name
    except KeyError:
        return {'error': 'Language code not recognized: {}'.format(language_code)}

    return language_name

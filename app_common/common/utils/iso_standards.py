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


def get_subdivision_name(subdivision_code):
    """
    :param subdivision_code:  ISO 3166, e.g. 'US-CA'
    :return: Subdivision name, e.g. "California"
    :rtype:  str
    """
    try:
        subdivision = pc.subdivisions.get(code=subdivision_code.upper())
        subdivision_name = subdivision.name
    except KeyError:
        return None

    return subdivision_name


def get_country_code_from_name(country_name):
    try:
        return pc.countries.get(name=country_name.capitalize()).alpha2
    except KeyError:
        pass
    try:
        return pc.countries.get(alpha3=country_name.upper()).alpha2
    except KeyError:
        pass
    try:
        return pc.countries.get(alpha2=country_name.upper()).alpha2
    except KeyError:
        return


def country_code_if_valid(country_code_or_name):
    """
    This function will return iso3166 standard country code only
    if the provided country-code or country-name is recognized
    :param country_code_or_name: str | iso country code or country name or country's official name
    :rtype: str
    Example:
        >>> # iso3166 alpha2 country code
        >>> country_code_if_valid('US')  # => 'US'
        >>> # iso3166 alpha3 country code
        >>> country_code_if_valid('USA')  # => 'US'
        >>> # country name
        >>> country_code_if_valid('United States')  # => 'US'
        >>> # country's official name
        >>> country_code_if_valid('United Sates of America')  # => 'US'
    """
    country_code_or_name = country_code_or_name.strip()

    try:
        country = pc.countries.get(alpha2=country_code_or_name)
    except KeyError:
        try:
            country = pc.countries.get(alpha3=country_code_or_name)
        except KeyError:
            try:
                country = pc.countries.get(name=country_code_or_name)
            except KeyError:
                try:
                    country = pc.countries.get(official_name=country_code_or_name)
                except KeyError:
                    country = None  # not found

    return country.alpha2 if country else ''

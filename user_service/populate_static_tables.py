"""
Functions for adding necessary records to static tables
"""
from user_service.common.models.db import db
from user_service.common.models.candidate import (
    CandidateStatus, ClassificationType, EmailLabel, PhoneLabel, RatingTag, SocialNetwork
)
from user_service.common.models.misc import Culture, Frequency, Product
from user_service.common.models.email_marketing import EmailClient


def create_candidate_status():
    """ Populates CandidateStatus table """
    statuses = [
        {'description': 'New', 'notes': 'Newly added candidate'},
        {'description': 'Contacted', 'notes': 'Candidate is contacted'},
        {'description': 'Unqualified', 'notes': 'Candidate is unqualified'},
        {'description': 'Qualified', 'notes': 'Candidate is qualified'},
        {'description': 'Prospect', 'notes': 'Candidate is a prospect'},
        {'description': 'Candidate', 'notes': 'Candidate is highly prospective'},
        {'description': 'Hired', 'notes': 'Candidate is hired'},
        {'description': 'Connector', 'notes': None}
    ]
    for status in statuses:
        candidate_status = CandidateStatus(description=status['description'], notes=status['notes'])
        db.session.add(candidate_status)
    db.session.commit()


def create_classification_types():
    """ Populates ClassificationType table """
    classifications = [
        {'code': 'Unspecified', 'description': 'Unspecified', 'notes': 'the degree is not specified'},
        {'code': 'Bachelors', 'description': 'Bachelors degree', 'notes': 'Bachelors degree, e.g. BS., BA., etc.'},
        {'code': 'Associate', 'description': 'Associate degree', 'notes': 'Undergraduate academic two-year degree'},
        {'code': 'Masters', 'description': "Master's degree", 'notes': "Master's degree, e.g. MSc., MA., etc."},
        {'code': 'Doctorate', 'description': "Doctorate degree", 'notes': "Doctorate degree e.g. PhD, EdD., etc."},
        {'code': 'Somehighschoolorequivalent', 'description': "Some high school or equivalent",
         'notes': "A high school drop out or equivalent level"},
        {'code': 'Highschoolorequivalent', 'description': "High school or equivalent",
         'notes': "A high school degree or equivalent"},
        {'code': 'Professional', 'description': "Professional", 'notes': None},
        {'code': 'Certification', 'description': "Certification", 'notes': None},
        {'code': 'Vocational', 'description': "Vocational", 'notes': None},
        {'code': 'Somecollege', 'description': "Some college", 'notes': None},
        {'code': 'Secondary', 'description': "Secondary", 'notes': None},
        {'code': 'GED', 'description': "GED", 'notes': None},
        {'code': 'Somepostgraduate', 'description': "Some postgraduate", 'notes': None}
    ]
    for classification in classifications:
        classification_type = ClassificationType(code=classification['code'],
                                                 description=classification['description'],
                                                 notes=classification['notes'])
        db.session.add(classification_type)
    db.session.commit()


def create_cultures():
    """ Populates Culture table """
    cultures = [
        {'description': 'English', 'code': 'en-us'}
    ]
    for culture in cultures:
        cult = Culture(description=culture['description'], code=culture['code'])
        db.session.add(cult)
    db.session.commit()


def create_email_clients():
    """ Populates EmailClient table """
    clients = [
        {'name': 'Outlook Plugin'}
    ]
    for client in clients:
        db.session.add(EmailClient(name=client['name']))
    db.session.commit()


def create_email_labels():
    """ Populates EmailLabel table """
    email_labels = [
        {'description': 'Primary'},
        {'description': 'Home'},
        {'description': 'Work'},
        {'description': 'Other'}
    ]
    for email_label in email_labels:
        db.session.add(EmailLabel(description=email_label['description']))
    db.session.commit()


def create_frequencies():
    """ Populates Frequency Table """
    frequencies = [
        {'name': 'Once'},
        {'name': 'Daily'},
        {'name': 'Weekly'},
        {'name': 'Biweekly'},
        {'name': 'Monthly'},
        {'name': 'Yearly'},
        {'name': 'Custom'}
    ]
    for frequency in frequencies:
        db.session.add(Frequency(name=frequency['name']))
    db.session.commit()


def create_phone_labels():
    """ Populates PhoneLabel Table """
    phone_labels = [
        {'description': 'Mobile'},
        {'description': 'Home'},
        {'description': 'Work'},
        {'description': 'Home Fax'},
        {'description': 'Work Fax'},
        {'description': 'Other'}
    ]
    for phone_label in phone_labels:
        db.session.add(PhoneLabel(description=phone_label['description']))
    db.session.commit()


def create_products():
    """ Populates Product Table """
    products = [
        {'name': 'Mobile', 'notes': 'Talent Mobile App [iPhone]'},
        {'name': 'Web', 'notes': 'Talent Website'},
        {'name': 'Widget', 'notes': 'Talent Web Widget'},
        {'name': 'OpenWeb', 'notes': 'Dice OpenWeb'}
    ]
    for product in products:
        db.session.add(Product(name=product['name'], notes=product['notes']))
    db.session.commit()


def create_rating_tags():
    """ Populates RatingTag Table """
    rating_tags = [
        {'description': 'Overall'},
        {'description': 'Presentation'},
        {'description': 'Communication Skill'},
        {'description': 'Interests'},
        {'description': 'Academic Experience'},
        {'description': 'Work Experience'}
    ]
    for rating_tag in rating_tags:
        db.session.add(RatingTag(description=rating_tag['description']))
    db.session.commit()


def create_social_networks():
    """ Populates SocialNetwork Table """
    social_networks = [
        {'name': 'Facebook', 'url': 'www.facebook.com/'},
        {'name': 'LinkedIn', 'url': 'www.linkedin.com/'},
        {'name': 'Twitter', 'url': 'https://twitter.com/'},
        {'name': 'Flickr', 'url': 'www.flickr.com/'},
        {'name': 'Friendster', 'url': 'www.friendster.com/'},
        {'name': 'Hi5', 'url': 'hi5.com/'},
        {'name': 'Pandora', 'url': 'www.pandora.com/'},
        {'name': 'MyLife', 'url': 'www.mylife.com/'},
        {'name': 'MySpace', 'url': 'www.myspace.com/'},
        {'name': 'Google+', 'url': 'https://plus.google.com/'},
        {'name': 'Tagged', 'url': 'tagged.com/'},
        {'name': 'Meetup', 'url': 'www.meetup.com/'},
        {'name': 'Dice', 'url': 'www.dice.com'},
        {'name': 'BlogSpot', 'url': 'www.blogspot.com'},
        {'name': 'StackOverflow', 'url': 'www.stackoverflow.com'},
        {'name': 'StackExchange', 'url': 'www.stackexchange.com'},
        {'name': 'Unknown', 'url': None},
        {'name': 'BitBucket', 'url': 'http://bitbucket.org'},
        {'name': 'Google', 'url': 'https://plus.google.com'},
        {'name': 'ServerFault', 'url': 'http://serverfault.com'},
        {'name': 'AskUbuntu', 'url': 'http://askubuntu.com'},
        {'name': 'YouTube', 'url': 'http://youtube.com'},
        {'name': 'GitHub', 'url': 'http://github.com'},
        {'name': 'Pinterest', 'url': 'http://pinterest.com'},
        {'name': 'Quora', 'url': 'http://quora.com'},
        {'name': 'last.fm', 'url': 'http://last.fm'},
        {'name': 'Tumblr', 'url': 'http://algodenada.tumblr.com'},
        {'name': 'FourSquare', 'url': 'https://foursquare.com'},
        {'name': 'Klout', 'url': 'http://klout.com'},
        {'name': 'AboutMe', 'url': 'http://about.me'},
        {'name': 'SuperUser', 'url': 'http://superuser.com'},
        {'name': 'LiveJournal', 'url': 'http://users.livejournal.com'},
        {'name': 'Stumbleupon', 'url': 'http://stumbleupon.com'},
        {'name': 'instagram', 'url': 'http://instagram.com'},
        {'name': 'FriendFeed', 'url': 'http://friendfeed.com'},
        {'name': 'Vimeo', 'url': 'http://vimeo.com'},
        {'name': 'Gravatar', 'url': 'http://gravatar.com'},
        {'name': 'Geek List', 'url': 'http://geekli.st'},
        {'name': 'Wordpress.com', 'url': 'http://ammarshaikh.wordpress.com'},
        {'name': 'MetaStackOverflow', 'url': 'http://meta.stackoverflow.com'},
        {'name': 'Behance', 'url': 'http://www.behance.net'},
        {'name': 'Elance', 'url': 'https://www.elance.com'},
        {'name': 'slideshare', 'url': 'http://slideshare.net'},
        {'name': 'lanyrd', 'url': 'http://lanyrd.com'},
        {'name': 'Disqus', 'url': 'http://disqus.com'},
        {'name': 'Angel List', 'url': 'https://angel.co'},
        {'name': 'Coroflot.com', 'url': 'http://coroflot.com'},
        {'name': 'Plancast', 'url': 'http://plancast.com'},
        {'name': 'delicious', 'url': 'http://delicious.com'},
        {'name': 'efinancialcareers', 'url': 'http://backoffice.efinancialcareers.com'},
        {'name': 'CrunchBase', 'url': 'http://crunchbase.com'},
        {'name': 'posterous', 'url': 'https://posterous.com'},
        {'name': 'SourceForge', 'url': 'http://sourceforge.net'},
        {'name': 'Sites Google', 'url': 'https://sites.google.com'},
        {'name': 'RIGZONE', 'url': 'http://www.rigzone.com'},
        {'name': 'Blogger', 'url': 'http://blogger.com'},
        {'name': 'BullhOrnReach', 'url': 'http://www.bullhornreach.com'},
        {'name': 'Plaxo', 'url': 'http://plaxo.com'},
        {'name': 'Reddit', 'url': 'http://reddit.com'},
        {'name': 'SunzuCom', 'url': 'http://www.sunzu.com'},
        {'name': 'Dribbble', 'url': 'http://dribbble.com'},
        {'name': 'Typepad', 'url': 'http://antsblog.typepad.com'},
        {'name': 'The IT Job Board', 'url': 'https://recruiters.theitjobboard.com'},
        {'name': 'LaunchPad', 'url': 'https://launchpad.net'},
        {'name': 'Identi.ca', 'url': 'http://identi.ca'},
        {'name': 'Stack Apps', 'url': 'http://stackapps.com'},
        {'name': 'Gitorious', 'url': 'http://gitorious.org'},
        {'name': 'Viadeo', 'url': 'http://viadeo.com'},
        {'name': 'Yelp', 'url': 'http://yelp.com'},
        {'name': 'qik', 'url': 'http://qik.com'},
        {'name': 'Area51StackExchange', 'url': 'http://area51.stackexchange.com'},
        {'name': 'MetaStackExchange', 'url': 'http://meta.stackexchange.com'},
        {'name': 'OILPRO', 'url': 'http://oilpro.com'},
        {'name': 'UnixStackExchange', 'url': 'http://unix.stackexchange.com'},
        {'name': 'AppleStackExchange', 'url': 'http://apple.stackexchange.com'},
        {'name': 'MoneyStackExchange', 'url': 'http://money.stackexchange.com'},
        {'name': 'UxStackExchange', 'url': 'http://ux.stackexchange.com'}
    ]
    for sn in social_networks:
        db.session.add(SocialNetwork(name=sn['name'], url=sn['url']))
    db.session.commit()
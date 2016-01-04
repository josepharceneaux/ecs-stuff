__author__ = 'erikfarmer'
import datetime
import random

from widget_service.common.models.misc import CustomField
from widget_service.common.models.university import University
from widget_service.common.models.misc import AreaOfInterest
from widget_service.common.models.misc import Culture
from widget_service.common.models.misc import Major
from widget_service.common.models.misc import Organization
from widget_service.common.models.user import Domain
from widget_service.common.models.widget import WidgetPage
from widget_service.common.utils.handy_functions import random_word
from widget_service.widget_app import db


# TODO add primary email label, phone label , custom fields (sub pref, nuid).
def fill_db():
    print 'Filling Database'
    RANDOM_CULTURE = Culture(description='random', code='rndmz')
    KAISER_UMBRELLA = Organization(name='Kaiser MEGA CORP')
    db.session.add(RANDOM_CULTURE)
    db.session.commit()
    db.session.add(KAISER_UMBRELLA)
    db.session.commit()
    KAISER_CORP = Domain(name='kaiser_corporate', usage_limitation=0,
                         expiration=datetime.datetime(2050, 4, 26),
                         added_time=datetime.datetime(2050, 4, 26),
                         organization_id=KAISER_UMBRELLA.id, is_fair_check_on=False, is_active=1,
                         default_tracking_code=1, default_from_name=('asd'),
                         default_culture_id=RANDOM_CULTURE.id,
                         settings_json='json', updated_time=datetime.datetime.now(),)
    KAISER_UNI = Domain(name='kaiser_university', usage_limitation=0,
                         expiration=datetime.datetime(2050, 4, 26),
                         added_time=datetime.datetime(2050, 4, 26),
                         organization_id=KAISER_UMBRELLA.id, is_fair_check_on=False, is_active=1,
                         default_tracking_code=1, default_from_name=('asd'),
                         default_culture_id=RANDOM_CULTURE.id,
                         settings_json='json', updated_time=datetime.datetime.now(),)
    KAISER_MIL = Domain(name='kaiser_military', usage_limitation=0,
                         expiration=datetime.datetime(2050, 4, 26),
                         added_time=datetime.datetime(2050, 4, 26),
                         organization_id=KAISER_UMBRELLA.id, is_fair_check_on=False, is_active=1,
                         default_tracking_code=1, default_from_name=('asd'),
                         default_culture_id=RANDOM_CULTURE.id,
                         settings_json='json', updated_time=datetime.datetime.now())
    DOMAINS = [KAISER_CORP, KAISER_UNI, KAISER_MIL]
    for d in DOMAINS:
        db.session.add(d)
    db.session.commit()
    corp_wp = WidgetPage(widget_name='kaiser_3.html')
    university_wp = WidgetPage(widget_name='kaiser_2.html')
    military_wp = WidgetPage(widget_name='kaiser_military.html')
    db.session.bulk_save_objects([corp_wp, university_wp, military_wp])
    print 'Finished creating Culture, Organization, Domains, WidgetPages'
    print 'Creating Majors and Areas of Interest'
    MAJORS = []
    for i in xrange(30):
        MAJORS.append(
            Major(name=random_word(12), domain_id=random.choice(DOMAINS).id)
        )
    db.session.bulk_save_objects(MAJORS)
    for d in DOMAINS:
        for i in xrange(10):
            aoi = AreaOfInterest(domain_id=d.id, description=random_word(4),
                                 parent_id=None)
            db.session.add(aoi)
            db.session.commit()
            for ii in xrange(4):
                sub_aoi = AreaOfInterest(domain_id=d.id, description='{}: {}'.format(aoi.description, random_word(6)),
                                 parent_id=aoi.id)
                db.session.add(sub_aoi)
                db.session.commit()
    UNIVERSITIES = []
    for i in xrange(10):
        UNIVERSITIES.append(
            University(name='University of {}'.format(random_word(6)))
        )
    db.session.bulk_save_objects(UNIVERSITIES)
    db.session.commit()





def destroy_db():
    print 'Murdering the local db'
    db.session.query(University).delete()
    db.session.commit()
    db.session.query(AreaOfInterest).filter(AreaOfInterest.parent_id!=None).delete()
    db.session.commit()
    db.session.query(AreaOfInterest).delete()
    db.session.commit()
    db.session.query(Major).delete()
    db.session.commit()
    db.session.query(Domain).delete()
    db.session.commit()
    db.session.query(Organization).delete()
    db.session.commit()
    db.session.query(Culture).delete()
    db.session.commit()
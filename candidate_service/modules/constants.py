"""
This module contains all constants related to Candidate De-Duping code
"""
EXACT = 100
HIGH = 90
MEDIUM_HIGH = 80
MEDIUM = 60
LOW = 40
LEVENSHTEIN_1 = MEDIUM
LEVENSHTEIN_2 = MEDIUM_HIGH
LEVENSHTEIN_3 = HIGH

MOBILE_SOURCE_PRODUCT_ID = 'MOBILE_SOURCE_PRODUCT_ID'
EXTENSION_SOURCE_PRODUCT_ID = 'EXTENSION_SOURCE_PRODUCT_ID'
MATCH_CATEGORIES = {
    'low': LOW,
    'medium': MEDIUM,
    'high': HIGH,
    'yes': EXACT
}

CATEGORIES_NAMES = ['yes', 'high', 'medium', 'low']

# Values are in seconds.
# Cache candidate for 6 hours or 21600 seconds
CANDIDATE_CACHE_TIMEOUT = 21600

YES_MATCH_CASES = [('email',), ('name_1', 'name_2', 'name_3', 'phone'), ('social_profile_url',)]
HIGH_MATCH_CASES = [
    ('name_1', 'name_2', 'name_3', 'job_title', 'job_description,%s' % MEDIUM),
    ('name_1', 'name_2', 'name_3', 'job_title', 'location_1', 'location_2'),
    ('name_1', 'name_2', 'name_3', 'job_title,%s' % MEDIUM, 'job_start_date'),
    ('name_1', 'name_2', 'name_3', 'job_title,%s' % MEDIUM, 'job_end_date'),
    ('name_1', 'name_2', 'name_3', 'job_title,%s' % MEDIUM, 'school', 'degree')
]

MEDIUM_MATCH_CASES = [
    ('name_1', 'name_2', 'location_1', 'location_2'),
    ('name_4', 'name_5', 'phone'),
    ('name_1', 'name_2', 'name_3', 'job_title,%s' % MEDIUM_HIGH, 'location_1', 'location_2'),
    ('name_1', 'name_2', 'name_3', 'job_description,%s' % MEDIUM_HIGH, 'location_1', 'location_2'),
    ('name_3', 'job_title'),
    ('name_3', 'job_description'),
    ('name_1', 'name_2', 'name_3', 'company'),
    ('name_4', 'name_5', 'phone', 'job_title'),
    ('name_4', 'name_5', 'phone', 'job_description')
]

LOW_MATCH_CASES = [
    ('name_1', 'name_2'),
    ('name_5,%s' % HIGH, 'location_2', 'location_3'),
    ('name_1,%s' % HIGH, 'name_2,%s' % HIGH, 'job_description'),
    ('name_1,%s' % HIGH, 'name_2,%s' % HIGH,'job_title'),
    ('name_4', 'job_title', 'job_description,%s' % HIGH),
    ('name_4', 'location_1'),
    ('name_4', 'school', 'degree'),
    ('name_4', 'company'),
    ('name_3', 'location_2', 'location_3'),
    ('name_4', 'job_title,%s' % MEDIUM, 'school'),
    ('name_4', 'job_title,%s' % MEDIUM, 'degree'),
]

JOB_TITLE_VARIATIONS = [
    ('Sr.|sr.', 'Senior'),
    ('Jr.|jr.', 'Junior'),
    ('VP |vp ', 'Vice President '),
    ('pres', 'President'),
    ('CTO |cto ', 'Chief Technical Officer '),
    ('CMO |cmo ', 'Chief Marketing Officer ')
]

ADDRESS_NOTATIONS = [
    (' street', ' st.', ' st', ''),
    (' avenue', ' ave.', ' ave'),
    (' boulevard', ' blvd.', ' blvd'),
    (' way', ' wy.', ' wy'),
    (' lane', ' ln', ' ln.'),
    (' court', ' ct.', ' ct'),
    (' loop', ' lp.', ' lp'),
    (' road', ' rd.', ' rd'),
    (' highway', ' hwy.', ' hyw')
]

DEGREES = [
    ('AA', 'A.A.', 'A.A', 'Associate of Arts'),
    ('MS', 'M.S.', 'M.S', 'Masters of Science'),
    ('BA', 'B.A.', 'B.A', 'Bachelor of Arts'),
    ('BABA', 'B.A.B.A.', 'Bach of Arts of Business Administration'),
    ('B.A.Com.', 'Bachelor of Arts in Communication'),
    ('BAE', 'B.A.E.', 'Bachelor of Arts in Education', 'Bachelor of Art Education'),
    ('BAE', 'B.A.E.', 'Bachelor of Aerospace Engineering'),
    ('B.Ag', 'Bachelor of Agriculture'),
    ('B.Arch.', 'B.Arch', 'Bachelor of Architecture'),
    ('BBA', 'B.B.A.', 'Bachelor of Business Administration'),
    ('BCE', 'B.C.E.', 'Bachelor of Civil Engineering'),
    ('B.Ch.E.', 'Bachelor of Chemical Engineering'),
    ('BD', 'B.D.', 'Bachelor of Divinity'),
    ('BE', 'B.E.', 'Bachelor of Education'),
    ('BE', 'B.E.', 'B.E', 'Bachelor of Engineering'),
    ('BEE', 'B.E.E.', 'Bachelor of Electrical Engineering'),
    ('BFA', 'B.F.A.', 'Bachelor of Fine Arts'),
    ('B.In.Dsn.', 'B.In.Dsn', 'Bachelor of Industrial Design'),
    ('BJ', 'B.J.', 'Bachelor of Journalism'),
    ('BLA', 'B.L.A.', 'Bachelor of Liberal Arts'),
    ('B.M.Ed', 'B.M.Ed.', 'Bachelor of Music Education'),
    ('B.Pharm', 'B.Pharm.', 'Bachelor of Pharmacy'),
    ('BS', 'B.S.', 'B.Sc', 'Bachelor of Science'),
    ('BSAE', 'B.S.A.E.', 'B.S. in Aerospace Engineering', 'BS in Aerospace Engineering'),
    ('BSBA', 'B.S.B.A.', 'B.S. in Business Administration', 'BS in Business Administration'),
    ('BSCS', 'B.S.C.S.', 'B.S. in Computer Science', 'BS in Computer Science'),
    ('B.S.Chem', 'B.S.Chem.', 'B.S. in Chemistry', 'BS in Chemistry'),
    ('BSE', 'B.S.E.', 'B.S. in Engineering', 'BS in Engineering'),
    ('BSEd', 'B.S.Ed', 'B.S.Ed.', 'B.S. in Education'),
    ('BSME', 'B.S.M.E.', 'B.S. in Mechanical Engineering'),
    ('B.S.Micr', 'B.S.Micr.', 'B.S. in Microbiology'),
    ('BSSW', 'B.S.S.W.', 'B.S.S.W', 'B.S. in Social Work'),
    ('PhB', 'Ph.B.', 'Bachelor of Philosophy'),
    ('Th.B', 'Th.B.', 'Bachelor of Theology'),

    # Master Degrees
    ('MA', 'M.A.', 'Master of Arts'),
    ('M.Acct', 'M.Acct.', 'Master of Accounting'),
    ('M.Aqua', 'M.Aqua.', 'Master of Aquaculture'),
    ('MBA', 'M.B.A.', 'M.B.A', 'Masters of Business Administration'),
    ('MCD', 'M.C.D.', 'Master of Communication Disorders'),
    ('MCS', 'M.C.S.', 'Master of Computer Science'),
    ('MDiv', 'M.Div.', 'Master of Divinity'),
    ('ME', 'M.E.', 'Master of Engineering'),
    ('MEd', 'M.Ed.', 'Master of Education'),
    ('MFstry', 'M.Fstry.', 'Master of Forestry'),
    ('MLArch', 'M.L.Arch.', 'Master of Landscape Architecture'),
    ('MLIS', 'M.L.I.S.', 'Master of Library & Information Studies'),
    ('MM', 'M.M.', 'M.Mus.', 'M.Mus', 'Master of Music'),
    ('MPS', 'M.P.S.', 'Master of Political Science'),
    ('MS', 'M.S.', 'Master of Science'),
    ('MSCJ', 'M.S.C.J.', 'M.S. in Criminal Justice'),
    ('MSCS', 'M.S.C.S.', 'M.S. in Computer Science'),
    ('MSChem', 'M.S.Chem.', 'M.S.Chem', 'M.S. in Chemistry'),
    ('MSFS', 'M.S.F.S.', 'M.S. in Forensic Science'),
    ('MSMSci', 'M.S.M.Sci.', 'M.S. in Marine Science'),
    ('MSMet', 'M.S.Met.', 'M.S.Met', 'M.S. in Metallurgical Engineering'),
    ('MSwE', 'M.Sw.E', 'Master of Software Engineering'),
    ('MSW', 'M.S.W.', 'Master of Social Work'),
    ('MTh', 'M.Th.', 'Master of Theology'),

    # Doctorate Abbreviations
    ('AuD', 'Au.D.', 'Au.D', 'Doctor of Audiology'),
    ('DA', 'D.A.', 'D.A', 'Doctor of Arts'),
    ('DBA', 'D.B.A.', 'D.B.A', 'Doctor of Business Administration'),
    ('DC', 'D.C.', 'D.C', 'Doctor of Chiropractic'),
    ('DD', 'D.D.', 'D.D', 'Doctor of Divinity'),
    ('DEd', 'D.Ed.', 'D.Ed', 'Doctor of Education'),
    ('DLS', 'D.L.S.', 'D.L.S', 'Doctor of Library Science'),
    ('DMA', 'D.M.A.', 'D.M.A', 'Doctor of Musical Arts'),
    ('DPA', 'D.P.A.', 'D.P.A', 'Doctor of Public Administration'),
    ('DPH', 'D.P.H.', 'D.P.H', 'Doctor of Public Health'),
    ('DSc', 'D.Sc.', 'D.Sc', 'Doctor of Science'),
    ('DSW', 'D.S.W.', 'D.S.W', 'Doctor of Social Welfare, Doctor of Social Work'),
    ('DVM', 'D.V.M.', 'D.V.M', 'Doctor of Veterinary Medicine'),
    ('EdD', 'Ed.D.', 'Ed.D', 'Doctor of Education'),
    ('JD', 'J.D.', 'J.D', 'Doctor of Jurisprudence', 'Doctor of Laws'),
    ('LHD', 'L.H.D.', 'L.H.D', 'Doctor of Humane Letters'),
    ('LLD', 'LL.D.', 'LL.D', 'Doctor of Laws'),
    ('DM', 'D.M.', 'D.M', 'Doctor of Music'),
    ('OD', 'O.D.', 'O.D', 'Doctor of Optimetry'),
    ('PhD', 'Ph.D.', 'Ph.D', 'Doctor of Philosophy'),
    ('SD', 'S.D.', 'S.D', 'ScD.', 'Sc.D.', 'Sc.D', 'Doctor of Science'),
    ('SScD', 'S.Sc.D.', 'S.Sc.D', 'Doctor of Social Science'),
    ('ThD', 'Th.D.', 'Th.D', 'Doctor of Theology'),

    # Common Medical Degree Abbreviations
    ('BN', 'B.N.', 'B.N', 'Bachelor of Nursing'),
    ('BSN', 'B.S.N.', 'B.S.N', 'B.S. in Nursing'),
    ('MN', 'M.N.', 'M.N', 'Master of Nursing'),
    ('MNA', 'M.N.A.', 'M.N.A', 'Master of Nurse Anesthesia'),
    ('DDS', 'D.D.S.', 'D.D.S', 'Doctor of Dental Surgery'),
    ('DMD', 'D.M.D.', 'D.M.D', 'Doctor of Dental Medicine, Doctor of Medical Dentistry'),
    ('DO', 'D.O.', 'D.O', 'Doctor of Osteopathic Medicine'),
    ('DPT', 'D.P.T.', 'D.P.T', 'Doctor of Physical Therapy'),
    ('DSN', 'D.S.N.', 'D.S.N', 'Doctor of Science in Nursing'),
    ('DScPT', 'D.Sc.PT.', 'D.Sc.PT', 'Doctor of Science in Physical Therapy'),
    ('MD', 'M.D.', 'M.D', 'Doctor of Medicine'),
    ('OD', 'O.D.', 'O.D', 'Doctor of Optometry'),
    ('PharmD', 'Pharm.D.', 'Pharm.D', 'Doctor of Pharmacy')
]

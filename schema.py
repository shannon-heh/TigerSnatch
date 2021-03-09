# ----------------------------------------------------------------------
# schema.py
# Contains tuples of keys that various database documents must contain.
# ----------------------------------------------------------------------

# all department codes, needed because MobileApp does not allow a
# wildcard query
# TODO: make this dynamic using scraping?
DEPT_CODES = ('AAS', 'AFS', 'AMS', 'ANT', 'AOS', 'APC', 'ARA', 'ARC',
              'ART', 'ASA', 'AST', 'ATL', 'BCS', 'CBE', 'CEE', 'CGS',
              'CHI', 'CHM', 'CHV', 'CLA', 'CLG', 'COM', 'COS', 'CWR',
              'CZE', 'DAN', 'EAS', 'ECO', 'ECS', 'EEB', 'EGR', 'ELE',
              'ENE', 'ENG', 'ENT', 'ENV', 'EPS', 'FIN', 'FRE', 'FRS',
              'GEO', 'GER', 'GHP', 'GSS', 'HEB', 'HIN', 'HIS', 'HLS',
              'HOS', 'HUM', 'ISC', 'ITA', 'JDS', 'JPN', 'JRN', 'KOR',
              'LAO', 'LAS', 'LAT', 'LIN', 'MAE', 'MAT', 'MED', 'MOD',
              'MOG', 'MOL', 'MPP', 'MSE', 'MTD', 'MUS', 'NES', 'NEU',
              'ORF', 'PAW', 'PER', 'PHI', 'PHY', 'POL', 'POP', 'POR',
              'PSY', 'QCB', 'REL', 'RES', 'RUS', 'SAN', 'SAS', 'SLA',
              'SML', 'SOC', 'SPA', 'SPI', 'STC', 'SWA', 'THR', 'TPP',
              'TRA', 'TUR', 'TWI', 'URB', 'URD', 'VIS', 'WRI')

# courses collection
COURSES_SCHEMA = ('courseid', 'displayname', 'title')
CLASS_SCHEMA = ('classid', 'section', 'type_name',
                'start_time', 'end_time', 'days')

# mappings collection
MAPPINGS_SCHEMA = ('displayname', 'title', 'courseid')

# enrollments collection
ENROLLMENTS_SCHEMA = ('classid', 'enrollment', 'capacity')

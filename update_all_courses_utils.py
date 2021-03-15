# ----------------------------------------------------------------------
# update_all_courses_utils.py
# Contains utilities for update_all_courses.py for the purpose of
# multiprocessing (top-level functions required).
# ----------------------------------------------------------------------

from mobileapp import MobileApp
from database import Database
from random import random

api = MobileApp()


def get_all_dept_codes(term):
    # hidden feature of MobileApp API (thanks to Jonathan Wilding
    # from OIT for helping us find this)
    res = api.get_courses(term=term, subject='list')

    try:
        codes = tuple([k['code'] for k in res['term'][0]['subjects']])
        codes[0] and codes[1]
    except:
        print('failed to get all department codes')
        exit(1)

    return codes


def process_dept_code(args):
    code, n, current_term_code, dummy_waitlists = args[0], args[1], args[2], args[3]
    db = Database()

    print('processing dept code', code)
    courses = api.get_courses(term=current_term_code, subject=code)

    if 'subjects' not in courses['term'][0]:
        raise RuntimeError('no query results')

    if n == 0:
        db.reset_db()

    # iterate through all subjects, courses, and classes
    for subject in courses['term'][0]['subjects']:
        for course in subject['courses']:
            courseid = course['course_id']
            if db.courses_contains_courseid(courseid):
                print('already processed courseid', courseid, '- skipping')
                continue

            # "new" will contain a single course document to be entered
            # in the courses (and, in part, the mapppings) collection
            new = {
                'courseid': courseid,
                'displayname': subject['code'] + course['catalog_number'],
                'title': course['title']
            }

            for x in course['crosslistings']:
                new['displayname'] += '/' + \
                    x['subject'] + x['catalog_number']

            print('inserting', new['displayname'], 'into mappings')
            db.add_to_mappings(new)

            all_new_classes = []
            lecture_idx = 0

            for class_ in course['classes']:
                meetings = class_['schedule']['meetings'][0]
                section = class_['section']

                # skip dummy sections (end with 99)
                if section.endswith('99'):
                    continue

                classid = class_['class_number']

                # new_class will contain a single lecture, precept,
                # etc. for a given course
                new_class = {
                    'classid': classid,
                    'section': section,
                    'type_name': class_['type_name'],
                    'start_time': meetings['start_time'],
                    'end_time': meetings['end_time'],
                    'days': ' '.join(meetings['days'])
                }

                # new_class_enrollment will contain enrollment and
                # capacity for a given class within a course
                new_class_enrollment = {
                    'classid': classid,
                    'courseid': courseid,
                    'enrollment': int(class_['enrollment']),
                    'capacity': int(class_['capacity'])
                }

                print('inserting', new['displayname'],
                      new_class['section'], 'into enrollments')
                db.add_to_enrollments(new_class_enrollment)

                # pre-recorded lectures are marked as 01:00 AM start
                if new_class['start_time'] == '01:00 AM':
                    new_class['start_time'] = 'Pre-Recorded'
                    new_class['end_time'] = ''

                # lectures should appear before other section types
                if class_['type_name'] == 'Lecture':
                    all_new_classes.insert(lecture_idx, new_class)
                    lecture_idx += 1
                else:
                    all_new_classes.append(new_class)

                # randomly add waitlists for testing purposes
                if dummy_waitlists and random() < 0.01:
                    print('inserting', classid, 'into waitlists')
                    db.add_to_waitlist(
                        'sheh', classid, disable_checks=True)

            for i, new_class in enumerate(all_new_classes):
                new[f'class_{i}'] = new_class

            print('inserting', new['displayname'], 'into courses')
            db.add_to_courses(new)

    print()

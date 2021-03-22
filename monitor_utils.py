# ----------------------------------------------------------------------
# monitor_utils.py
# Contains utilities for the Monitor class for the purpose of
# multiprocessing (top-level functions required).
# ----------------------------------------------------------------------

from mobileapp import MobileApp
from coursewrapper import CourseWrapper
from sys import exit
from database import Database

api = MobileApp()
_db = Database()


def get_latest_term():
    terms = api.get_terms()

    try:
        return terms['term'][0]['code']
    except:
        print('failed to get current term code')
        exit(1)


def get_new_mobileapp_data(term, course, classes):
    data = api.get_courses(term=term, search=course)

    if 'subjects' not in data['term'][0]:
        raise RuntimeError('no query results')

    new_enroll = {}
    new_cap = {}

    # O(n^2) loop - there is only one subject and course!
    for classid in classes:
        for subject in data['term'][0]['subjects']:
            for course in subject['courses']:
                for class_ in course['classes']:
                    if class_['class_number'] == classid:
                        new_enroll[classid] = int(class_['enrollment'])
                        new_cap[classid] = int(class_['capacity'])
                        break

    return new_enroll, new_cap


# returns course data and parses its data into dictionaries
# ready to be inserted into database collections

def get_course_in_mobileapp(term, course, curr_time):
    data = api.get_courses(term=term, search=course)

    if 'subjects' not in data['term'][0]:
        raise RuntimeError('no query results')

    new_enroll = {}
    new_cap = {}

    # iterate through all subjects, courses, and classes
    for subject in data['term'][0]['subjects']:
        for course in subject['courses']:
            courseid = course['course_id']

            new = {
                'courseid': courseid,
                'displayname': subject['code'] + course['catalog_number'],
                'title': course['title'],
                'time': curr_time}

            for x in course['crosslistings']:
                new['displayname'] += '/' + \
                    x['subject'] + x['catalog_number']

            new_mapping = new.copy()
            del new['time']

            all_new_classes = []
            lecture_idx = 0

            for class_ in course['classes']:
                meetings = class_['schedule']['meetings'][0]
                section = class_['section']

                # skip dummy sections (end with 99)
                if section.endswith('99'):
                    continue

                classid = class_['class_number']

                new_class = {
                    'classid': classid,
                    'section': section,
                    'type_name': class_['type_name'],
                    'start_time': meetings['start_time'],
                    'end_time': meetings['end_time'],
                    'days': ' '.join(meetings['days'])
                }

                new_enroll[classid] = int(class_['enrollment'])
                new_cap[classid] = int(class_['capacity'])

                new_class_enrollment = {
                    'classid': classid,
                    'courseid': courseid,
                    'section': section,
                    'enrollment': int(class_['enrollment']),
                    'capacity': int(class_['capacity'])
                }

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

            for i, new_class in enumerate(all_new_classes):
                new[f'class_{i}'] = new_class

    return new, new_mapping, new_enroll, new_cap


def process(args):
    term, course, classes = args[0], args[1], args[2]

    print('processing', course, 'with classes', classes)
    new_enroll, new_cap = get_new_mobileapp_data(term, course, classes)
    course_data = CourseWrapper(course, new_enroll, new_cap)
    print(course_data)
    return course_data

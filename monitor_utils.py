# ----------------------------------------------------------------------
# monitor_utils.py
# Contains utilities for the Monitor class for the purpose of
# multiprocessing (top-level functions required).
# ----------------------------------------------------------------------

from mobileapp import MobileApp
from coursewrapper import CourseWrapper
from sys import exit

api = MobileApp()


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


def process(args):
    term, course, classes = args[0], args[1], args[2]

    print('processing', course, 'with classes', classes)
    new_enroll, new_cap = get_new_mobileapp_data(term, course, classes)
    course_data = CourseWrapper(course, new_enroll, new_cap)
    print(course_data)
    return course_data

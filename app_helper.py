# ----------------------------------------------------------------------
# app_helper.py
# Defines helper methods to construct endpoints.
# ----------------------------------------------------------------------

from database import Database
from monitor import Monitor

_db = Database()
_monitor = Monitor()


# searches for course based on user query
def do_search(query):
    res = []
    if query.strip() == "":
        res = None
    else:
        query = query.replace(' ', '')
        res = _db.search_for_course(query)

    return res


# pulls most recent course info and returns dictionary with
# course details and list with class info
def pull_course(courseid):

    if courseid is None or courseid == "" or _db.get_course(courseid) is None:
        return None, None

    # updates course info if it has been 2 minutes since last update
    _monitor.pull_course_updates(courseid)

    course = _db.get_course_with_enrollment(courseid)

    # split course data into basic course details, and list of classes
    # with enrollmemnt data
    course_details = {}
    classes_list = []
    for key in course.keys():
        if key.startswith('class_'):
            classes_list.append(course[key])
        else:
            course_details[key] = course[key]

    return course_details, classes_list

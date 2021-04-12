# ----------------------------------------------------------------------
# app_helper.py
# Defines helper methods to construct endpoints.
# ----------------------------------------------------------------------

from database import Database
from monitor import Monitor
import re


MAX_QUERY_LENGTH = 150


def validate_query(query):
    if len(query) > MAX_QUERY_LENGTH:
        return False
    return re.match('^[^0-9a-zA-Z ]+$', query)


# searches for course based on user query
def do_search(query):
    res = []
    if query.strip() == "":
        res = None
    else:
        query = query.replace(' ', '')
        res = Database().search_for_course(query)

    return res


# pulls most recent course info and returns dictionary with
# course details and list with class info
def pull_course(courseid):

    if courseid is None or courseid == "" or Database().get_course(courseid) is None:
        return None, None

    # updates course info if it has been 2 minutes since last update
    Monitor().pull_course_updates(courseid)
    db = Database()
    course = db.get_course_with_enrollment(courseid)

    # split course data into basic course details, and list of classes
    # with enrollmemnt data
    course_details = {}
    classes_list = []
    for key in course.keys():
        if key.startswith('class_'):
            curr_class = course[key]
            try:
                waitlist_count = db.get_class_waitlist_size(
                    curr_class['classid'])
            except Exception:
                waitlist_count = 0
            curr_class['wl_size'] = waitlist_count
            classes_list.append(curr_class)
        else:
            course_details[key] = course[key]

    return course_details, classes_list


# parses through user's logs and constructs formatted strings
def construct_user_logs(netid):
    _db = Database()
    log_strs = _db.get_user_log(netid)
    user_logs = []
    for log in log_strs:
        log_details = log.split(",")
        time = log_details[0]
        deptnum = log_details[1]
        sectionname = log_details[2]
        n_new_spots = log_details[3]
        log_str = f"{time}: {n_new_spots} available in {sectionname} of {deptnum}"
        user_logs.append(log_str)
    return user_logs

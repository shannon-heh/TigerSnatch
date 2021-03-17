# ----------------------------------------------------------------------
# api.py
# Defines endpoints for TigerSnatch app.
# ----------------------------------------------------------------------

from flask import Flask
from flask import render_template, make_response, request, redirect, url_for
from database import Database
from CASClient import CASClient
from config import APP_SECRET_KEY
from waitlist import Waitlist

app = Flask(__name__, template_folder='./templates')
app.secret_key = APP_SECRET_KEY
_CAS = CASClient()  # need to test if this is acceptable (global CAS obj)
_db = Database()


# private method that redirects to landinage page
# if user is not logged in with CAS
# or if user is logged in with CAS, but doesn't have entry in DB

def redirect_landing():
    return not _CAS.is_logged_in() or not _db.is_user_created(_CAS.authenticate())


@app.route('/', methods=['GET'])
def index():
    if redirect_landing():
        return redirect(url_for('landing'))
    return redirect(url_for('dashboard'))


@app.route('/landing', methods=['GET', 'POST'])
def landing():
    html = render_template('landing.html')
    response = make_response(html)
    return response


@app.route('/login', methods=['GET'])
def login():
    netid = _CAS.authenticate()
    if not _db.is_user_created(netid):
        _db.create_user(netid)

    return redirect(url_for('dashboard'))


@app.route('/dashboard', methods=['GET'])
def dashboard():
    if redirect_landing():
        return redirect(url_for('landing'))

    netid = _CAS.authenticate()

    query = request.args.get('query')
    if query is not None:
        res = _db.search_for_course(query)
        html = render_template('index.html',
                               search_res=res,
                               last_query=query,
                               username=netid)
    else:
        html = render_template('index.html', username=netid)

    response = make_response(html)
    return response

# ----------------------------------------------------------------------


# @ app.route('/search', methods=['GET'])
# def search():
#     query = request.args.get('query')

#     res = _db.search_for_course(query)

#     html = render_template('index.html',
#                            search_res=res)
#     response = make_response(html)
#     return response

# ----------------------------------------------------------------------


@ app.route('/course', methods=['GET'])
def get_course():
    if not _CAS.is_logged_in():
        return redirect(url_for('landing'))

    netid = _CAS.authenticate()
    courseid = request.args.get('courseid')
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

    html = render_template('course.html',
                           netid=netid,
                           course_details=course_details,
                           classes_list=classes_list)
    response = make_response(html)
    return response


@app.route('/logout', methods=['GET'])
def logout():
    _CAS.logout()
    return redirect(url_for('landing'))


@app.route('/add_to_waitlist', methods=['GET'])
def add_to_waitlist():
    classid = request.args.get('classid')
    netid = _CAS.authenticate()
    waitlist = Waitlist(netid)
    return str(waitlist.add_to_waitlist(classid))


@app.route('/remove_from_waitlist', methods=['GET'])
def remove_from_waitlist():
    classid = request.args.get('classid')
    netid = _CAS.authenticate()
    waitlist = Waitlist(netid)
    return str(waitlist.remove_from_waitlist(classid))

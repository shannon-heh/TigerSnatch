# ----------------------------------------------------------------------
# api.py
# Defines endpoints for TigerSnatch app.
# ----------------------------------------------------------------------

from flask import Flask
from flask import render_template, make_response, request, redirect, url_for, jsonify
from werkzeug.exceptions import HTTPException
from database import Database
from CASClient import CASClient
from config import APP_SECRET_KEY
from waitlist import Waitlist
from monitor import Monitor
from email.utils import parseaddr

app = Flask(__name__, template_folder='./templates')
app.secret_key = APP_SECRET_KEY
_CAS = CASClient()
_db = Database()
_monitor = Monitor()


@app.errorhandler(Exception)
def handle_exception(e):
    # pass through HTTP errors
    if isinstance(e, HTTPException):
        return e

    print(e)

    # non-HTTP exceptions only
    return render_template('error.html'), 500


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
    return make_response(html)


@app.route('/login', methods=['GET'])
def login():
    netid = _CAS.authenticate()
    if not _db.is_user_created(netid):
        _db.create_user(netid)

    return redirect(url_for('dashboard'))


@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if redirect_landing():
        return redirect(url_for('landing'))

    netid = _CAS.authenticate()

    data = _db.get_dashboard_data(netid)

    query = request.args.get('query')

    new_email = request.form.get('new_email')
    if query is not None and query != "":
        query = query.replace(' ', '')
        res = _db.search_for_course(query)
        email = _db.get_user(netid)['email']
        html = render_template('dashboard.html',
                               search_res=res,
                               last_query=query,
                               username=netid.rstrip(), data=data, email=email)
    elif new_email is not None:
        _db.update_user(netid, new_email.strip())
        email = _db.get_user(netid)['email']
        html = render_template(
            'dashboard.html', username=netid.rstrip(), data=data, email=email)
    else:
        email = _db.get_user(netid)['email']
        html = render_template(
            'dashboard.html', username=netid.rstrip(), data=data, email=email)
    return make_response(html)


@app.route('/about', methods=['GET'])
def about():
    if redirect_landing():
        return redirect(url_for('landing'))

    netid = _CAS.authenticate()

    html = render_template('about.html')
    return make_response(html)


@ app.route('/course', methods=['GET'])
def get_course():
    if not _CAS.is_logged_in():
        return redirect(url_for('landing'))

    netid = _CAS.authenticate()

    courseid = request.args.get('courseid')
    query = request.args.get('query')

    # if URL has no query param
    if query is not None and query != "":
        query = query.replace(' ', '')
        res = _db.search_for_course(query)
    else:
        res = None
        query = ""

    # if URL has no courseid param, courseid is empty string, or
    # courseid is invalid
    if courseid is None or courseid == "" or _db.get_course(courseid) is None:
        course_details = None
        html = render_template('course.html',
                               netid=netid,
                               course_details=course_details,
                               search_res=res,
                               last_query=query)

        response = make_response(html)
        return response

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

    curr_waitlists = _db.get_user(netid)['waitlists']

    html = render_template('course.html',
                           netid=netid,
                           course_details=course_details,
                           classes_list=classes_list,
                           curr_waitlists=curr_waitlists,
                           search_res=res,
                           last_query=query)

    return make_response(html)


@app.route('/logout', methods=['GET'])
def logout():
    _CAS.logout()
    return redirect(url_for('landing'))


@app.route('/add_to_waitlist/<classid>', methods=['POST'])
def add_to_waitlist(classid):
    netid = _CAS.authenticate()
    waitlist = Waitlist(netid)
    return jsonify({"isSuccess": waitlist.add_to_waitlist(classid)})


@ app.route('/remove_from_waitlist/<classid>', methods=['POST'])
def remove_from_waitlist(classid):
    netid = _CAS.authenticate()
    waitlist = Waitlist(netid)
    return jsonify({"isSuccess": waitlist.remove_from_waitlist(classid)})

# ----------------------------------------------------------------------
# api.py
# Defines endpoints for TigerSnatch app
# ----------------------------------------------------------------------

from flask import Flask
from flask import render_template, make_response, request, redirect, url_for
from database import Database
from CASClient import CASClient
from config import APP_SECRET_KEY

app = Flask(__name__, template_folder='./templates')
app.secret_key = APP_SECRET_KEY
CAS = CASClient()  # need to test if this is acceptable (global CAS obj)


# private method that redirects to landinage page
# if user is not logged in with CAS
# or if user is logged in with CAS, but doesn't have entry in DB

def redirect_landing():
    db = Database()
    if not CAS.is_logged_in() or not db.is_user_created(CAS.authenticate()):
        return redirect(url_for('landing'))


@app.route('/', methods=['GET'])
def index():
    redirect_landing()
    return redirect(url_for('dashboard'))


@app.route('/landing', methods=['GET', 'POST'])
def landing():
    html = render_template('landing.html')
    response = make_response(html)
    return response


@app.route('/login', methods=['GET'])
def login():
    netid = CAS.authenticate()
    db = Database()
    if not db.is_user_created(netid):
        db.create_user(netid)

    return redirect(url_for('dashboard'))


@app.route('/dashboard', methods=['GET'])
def dashboard():
    redirect_landing()
    netid = CAS.authenticate()

    query = request.args.get('query')
    if query is not None:
        res = db.search_for_course(query)
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

#     db = Database()
#     res = db.search_for_course(query)

#     html = render_template('index.html',
#                            search_res=res)
#     response = make_response(html)
#     return response

# ----------------------------------------------------------------------


@ app.route('/course', methods=['GET'])
def get_course():
    if not CAS.is_logged_in():
        return redirect(url_for('landing'))

    username = CAS.authenticate()
    courseid = request.args.get('courseid')
    db = Database()
    course = db.get_course_with_enrollment(courseid)

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
                           course_details=course_details,
                           classes_list=classes_list)
    response = make_response(html)
    return response


@app.route('/logout', methods=['GET'])
def logout():
    CAS.logout()
    return redirect(url_for('landing'))

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


@app.route('/', methods=['GET'])
def index():
    return redirect(url_for('dashboard'))


@app.route('/dashboard', methods=['GET'])
def dashboard():
    username = CASClient().authenticate()
    query = request.args.get('query')
    if query is not None:
        db = Database()
        res = db.search_for_course(query)
        html = render_template('index.html',
                               search_res=res,
                               last_query=query,
                               username=username)
    else:
        html = render_template('index.html', username=username)

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
    casClient = CASClient()
    username = casClient.authenticate()
    casClient.logout()
    html = render_template('index.html',
                           username=username)

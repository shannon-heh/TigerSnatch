# ----------------------------------------------------------------------
# api.py
# Defines endpoints for TigerSnatch app
# ----------------------------------------------------------------------

from flask import Flask
from flask import render_template, make_response, request
from database import Database

app = Flask(__name__, template_folder='./templates')


@app.route('/', methods=['GET'])
@app.route('/dashboard', methods=['GET'])
def index():
    html = render_template('index.html')
    response = make_response(html)
    return response

# ----------------------------------------------------------------------


@ app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query')
    db = Database()
    res = db.search_for_course(query)

    html = render_template('index.html',
                           search_res=res)
    response = make_response(html)
    return response

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
# ----------------------------------------------------------------------
# api.py
# Defines endpoints for TigerSnatch app.
# ----------------------------------------------------------------------

from flask import Flask
from flask import render_template, make_response, request, redirect, url_for, jsonify
from database import Database
from CASClient import CASClient
from config import APP_SECRET_KEY
from waitlist import Waitlist
from _exec_update_all_courses import do_update_async
from app_helper import do_search, pull_course, is_admin
from urllib.parse import quote_plus, unquote_plus
from sys import stderr
import traceback
import logging

app = Flask(__name__, template_folder='./templates')
app.secret_key = APP_SECRET_KEY
log = logging.getLogger('werkzeug')
log.disabled = True
_CAS = CASClient()


@app.errorhandler(Exception)
def handle_exception(e):
    traceback.print_exc()
    print(e)
    return render_template('error.html')


# private method that redirects to landing page
# if user is not logged in with CAS
# or if user is logged in with CAS, but doesn't have entry in DB
def redirect_landing():
    return not _CAS.is_logged_in() or not Database().is_user_created(_CAS.authenticate())


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
    _db = Database()

    netid = _CAS.authenticate()
    netid = netid.rstrip()
    if _db.is_blacklisted(netid):
        _db._add_admin_log(
            f'blacklisted user {netid} attempted to access the app')
        return make_response(render_template('blacklisted.html'))

    if not _db.is_user_created(netid):
        _db.create_user(netid)
        return redirect(url_for('tutorial'))

    print('user', netid, 'logged in')

    return redirect(url_for('dashboard'))


@app.route('/tutorial', methods=['GET'])
def tutorial():
    # if redirect_landing():
    #     return redirect(url_for('landing'))
    # html = render_template('tutorial.html')
    # return make_response(html)
    if redirect_landing():
        html = render_template('tutorial.html', loggedin=False)
        return make_response(html)

    html = render_template('tutorial.html',
                           user_is_admin=is_admin(CASClient().authenticate()),
                           loggedin=True,
                           notifs_online=Database().get_cron_notification_status())
    return make_response(html)


@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if redirect_landing():
        return redirect(url_for('landing'))

    print(request.headers.get('X-Forwarded-Proto'))

    _db = Database()
    netid = _CAS.authenticate()
    netid = netid.rstrip()
    if _db.is_blacklisted(netid):
        _db._add_admin_log(
            f'blacklisted user {netid} attempted to access the app')
        return make_response(render_template('blacklisted.html'))
    print('user', netid, 'viewed dashboard')

    data = _db.get_dashboard_data(netid)
    email = _db.get_user(netid, 'email')

    query = request.args.get('query')
    new_email = request.form.get('new_email')

    if query is None:
        query = ''
    search_res = do_search(query)

    if new_email is not None:
        if '<' in new_email or '>' in new_email or 'script' in new_email:
            print('HTML code detected in', new_email, file=stderr)
            return redirect(url_for('dashboard'))

        _db.update_user(netid, new_email.strip())
        return redirect(url_for('dashboard'))

    curr_sections = _db.get_current_sections(netid)

    html = render_template('base.html',
                           is_dashboard=True,
                           is_admin=False,
                           netid=netid,
                           user_is_admin=is_admin(netid),
                           search_res=search_res,
                           last_query=quote_plus(query),
                           last_query_unquoted=unquote_plus(query),
                           username=netid.rstrip(),
                           data=data,
                           email=email,
                           curr_sections=curr_sections,
                           notifs_online=_db.get_cron_notification_status())

    return make_response(html)


@app.route('/about', methods=['GET'])
def about():
    if redirect_landing():
        html = render_template('about.html', loggedin=False)
        return make_response(html)

    html = render_template('about.html',
                           user_is_admin=is_admin(CASClient().authenticate()),
                           loggedin=True,
                           notifs_online=Database().get_cron_notification_status())
    return make_response(html)


@app.route('/activity', methods=['GET'])
def activity():
    if redirect_landing():
        return redirect(url_for('landing'))

    netid = _CAS.authenticate()

    _db = Database()
    waitlist_logs = _db.get_user_waitlist_log(netid)
    trade_logs = _db.get_user_trade_log(netid)

    html = render_template('activity.html',
                           user_is_admin=is_admin(CASClient().authenticate()),
                           loggedin=True,
                           waitlist_logs=waitlist_logs,
                           trade_logs=trade_logs,
                           notifs_online=Database().get_cron_notification_status())

    return make_response(html)


@app.route('/searchresults', methods=['POST'])
@app.route('/searchresults/<query>', methods=['POST'])
def get_search_results(query=''):
    res = do_search(query)
    html = render_template('search/search_results.html',
                           last_query=quote_plus(query),
                           last_query_unquoted=unquote_plus(query),
                           search_res=res)
    return make_response(html)


@app.route('/courseinfo/<courseid>', methods=['POST'])
def get_course_info(courseid):
    _db = Database()
    netid = _CAS.authenticate()

    course_details, classes_list = pull_course(courseid)
    curr_waitlists = _db.get_user(netid, 'waitlists')
    section_names = _db.get_section_names_in_course(courseid)
    current_section = _db.get_current_section(netid, courseid)
    current_sectionname = _db.classid_to_sectionname(
        current_section) if current_section is not None else ''
    trade_unavailable = False
    if not section_names or len(section_names) < 2:
        trade_unavailable = True

    num_full = sum(class_data['isFull'] for class_data in classes_list)
    term_code = _db.get_current_term_code()

    html = render_template('course/course.html',
                           netid=netid,
                           user_is_admin=is_admin(netid),
                           courseid=courseid,
                           course_details=course_details,
                           classes_list=classes_list,
                           trade_unavailable=trade_unavailable,
                           num_full=num_full,
                           current_section=current_section,
                           current_sectionname=current_sectionname,
                           term_code=term_code,
                           curr_waitlists=curr_waitlists,
                           section_names=section_names,
                           notifs_online=_db.get_cron_notification_status())
    return make_response(html)


@app.route('/course', methods=['GET'])
def get_course():
    if not _CAS.is_logged_in():
        return redirect(url_for('landing'))

    _db = Database()

    netid = _CAS.authenticate()
    netid = netid.rstrip()
    if _db.is_blacklisted(netid):
        _db._add_admin_log(
            f'blacklisted user {netid} attempted to access the app')
        return make_response(render_template('blacklisted.html'))

    courseid = request.args.get('courseid')
    query = request.args.get('query')

    if query is None:
        query = ''

    search_res = do_search(query)

    course_details, classes_list = pull_course(courseid)
    curr_waitlists = _db.get_user(netid, 'waitlists')
    num_full = sum(class_data['isFull'] for class_data in classes_list)
    term_code = _db.get_current_term_code()
    section_names = _db.get_section_names_in_course(courseid)
    current_section = _db.get_current_section(netid, courseid)
    current_sectionname = _db.classid_to_sectionname(
        current_section) if current_section is not None else ''
    trade_unavailable = False
    if not section_names or len(section_names) < 2:
        trade_unavailable = True

    # change to check if updateSearch == 'false'
    # if updateSearch is None:
    html = render_template('base.html',
                           is_dashboard=False,
                           is_admin=False,
                           user_is_admin=is_admin(netid),
                           netid=netid,
                           current_section=current_section,
                           current_sectionname=current_sectionname,
                           courseid=courseid,
                           course_details=course_details,
                           classes_list=classes_list,
                           trade_unavailable=trade_unavailable,
                           curr_waitlists=curr_waitlists,
                           search_res=search_res,
                           num_full=num_full,
                           section_names=section_names,
                           term_code=term_code,
                           last_query=quote_plus(query),
                           last_query_unquoted=unquote_plus(query),
                           notifs_online=_db.get_cron_notification_status())

    return make_response(html)


@app.route('/logout', methods=['GET'])
def logout():
    _CAS.logout()
    return redirect(url_for('landing'))


@app.route('/add_to_waitlist/<classid>', methods=['POST'])
def add_to_waitlist(classid):
    netid = _CAS.authenticate()
    waitlist = Waitlist(netid)
    return jsonify({'isSuccess': waitlist.add_to_waitlist(classid)})


@app.route('/remove_from_waitlist/<classid>', methods=['POST'])
def remove_from_waitlist(classid):
    netid = _CAS.authenticate()
    waitlist = Waitlist(netid)
    return jsonify({'isSuccess': waitlist.remove_from_waitlist(classid)})


@app.route('/admin', methods=['GET', 'POST'])
def admin():
    netid = _CAS.authenticate()
    netid = netid.strip()
    try:
        if not is_admin(netid):
            return redirect(url_for(''))
    except:
        return redirect(url_for(''))

    print('admin', netid, 'viewed admin panel')

    _db = Database()
    admin_logs = _db.get_admin_logs()
    try:
        admin_logs = admin_logs['logs']
    except:
        admin_logs = None
    query = request.args.get('query-netid')

    if query is None:
        query = ''
    search_res = _db.search_for_user(query)

    html = render_template('base.html',
                           is_dashboard=False,
                           is_admin=True,
                           user_is_admin=True,
                           search_res=search_res,
                           last_query=quote_plus(query),
                           last_query_unquoted=unquote_plus(query),
                           username=netid.rstrip(),
                           admin_logs=admin_logs,
                           blacklist=_db.get_blacklist(),
                           notifs_online=_db.get_cron_notification_status(),
                           current_term_code=_db.get_current_term_code())

    return make_response(html)


@app.route('/add_to_blacklist/<user>', methods=['GET', 'POST'])
def add_to_blacklist(user):
    netid = _CAS.authenticate()
    netid = netid.strip()
    try:
        if not is_admin(netid):
            return redirect(url_for('landing'))
    except:
        return redirect(url_for('landing'))

    return jsonify({'isSuccess': Database().add_to_blacklist(user.strip())})


@app.route('/remove_from_blacklist/<user>', methods=['POST'])
def remove_from_blacklist(user):
    netid = _CAS.authenticate()
    netid = netid.strip()
    try:
        if not is_admin(netid):
            return redirect(url_for('landing'))
    except:
        return redirect(url_for('landing'))

    return jsonify({'isSuccess': Database().remove_from_blacklist(user.strip())})


@app.route('/get_notifications_status', methods=['POST'])
def get_notifications_status():
    if redirect_landing():
        return redirect(url_for('landing'))

    netid = _CAS.authenticate()
    netid = netid.strip()
    try:
        if not is_admin(netid):
            return redirect(url_for('landing'))
    except:
        return redirect(url_for('landing'))

    return jsonify({'isOn': Database().get_cron_notification_status()})


@app.route('/set_notifications_status/<status>', methods=['POST'])
def set_notifications_status(status):
    netid = _CAS.authenticate()
    netid = netid.strip()
    try:
        if not is_admin(netid):
            return redirect(url_for('landing'))
    except:
        return redirect(url_for('landing'))

    Database().set_cron_notification_status(status == 'true')
    return jsonify({})


@app.route('/clear_all_trades', methods=['POST'])
def clear_all_trades():
    netid = _CAS.authenticate()
    netid = netid.strip()
    try:
        if not is_admin(netid):
            return redirect(url_for('landing'))
    except:
        return redirect(url_for('landing'))

    return jsonify({'isSuccess': Database().clear_all_trades()})


@app.route('/clear_all_user_logs', methods=['POST'])
def clear_all_user_logs():
    netid = _CAS.authenticate()
    netid = netid.strip()
    try:
        if not is_admin(netid):
            return redirect(url_for('landing'))
    except:
        return redirect(url_for('landing'))

    return jsonify({'isSuccess': Database().clear_all_user_logs()})


@app.route('/update_all_courses', methods=['POST'])
def update_all_courses():
    netid = _CAS.authenticate()
    netid = netid.strip()
    try:
        if not is_admin(netid):
            return redirect(url_for('landing'))
    except:
        return redirect(url_for('landing'))

    do_update_async()  # CAUTION: hard reset and update

    return jsonify({})


@app.route('/clear_all_waitlists', methods=['POST'])
def clear_all_waitlists():
    netid = _CAS.authenticate()
    netid = netid.strip()
    try:
        if not is_admin(netid):
            return redirect(url_for('landing'))
    except:
        return redirect(url_for('landing'))

    return jsonify({'isSuccess': Database().clear_all_waitlists()})


@app.route('/clear_by_class/<classid>', methods=['POST'])
def clear_by_class(classid):
    netid = _CAS.authenticate()
    netid = netid.strip()
    try:
        if not is_admin(netid):
            return redirect(url_for('landing'))
    except:
        return redirect(url_for('landing'))

    return jsonify({'isSuccess': Database().clear_class_waitlist(classid)})


@app.route('/clear_by_course/<courseid>', methods=['POST'])
def clear_by_course(courseid):
    netid = _CAS.authenticate()
    netid = netid.strip()
    try:
        if not is_admin(netid):
            return redirect(url_for('landing'))
    except:
        return redirect(url_for('landing'))

    return jsonify({'isSuccess': Database().clear_course_waitlists(courseid)})


@app.route('/get_user_data/<netid>/<isTrade>', methods=['POST'])
def get_user_data(netid, isTrade):
    netid_ = _CAS.authenticate()
    netid_.strip()
    try:
        if not is_admin(netid_):
            return redirect(url_for('landing'))
    except:
        return redirect(url_for('landing'))

    return jsonify({'data': Database().get_waited_sections(netid.strip(),
                                                           trades=isTrade == 'true')})


@app.route('/update_user_section/<courseid>/<classid>', methods=['POST'])
def update_user_section(courseid, classid):
    netid = _CAS.authenticate()
    netid = netid.rstrip()
    status = Database().update_current_section(netid, courseid, classid)
    return jsonify({'isSuccess': status})


@app.route('/remove_user_section/<courseid>', methods=['POST'])
def remove_user_section(courseid):
    netid = _CAS.authenticate()
    netid = netid.rstrip()
    status = Database().remove_current_section(netid, courseid)
    return jsonify({'isSuccess': status})


@app.route('/find_matches/<courseid>', methods=['POST'])
def find_matches(courseid):
    netid = _CAS.authenticate()
    netid = netid.rstrip()
    matches = Database().find_matches(netid.strip(), courseid)
    return jsonify({'data': matches})


@app.route('/contact_trade/<course_name>/<match_netid>/<section_name>', methods=['POST'])
def contact_trade(course_name, match_netid, section_name):
    netid = _CAS.authenticate()
    netid = netid.rstrip()
    log_str = f'You contacted {match_netid} to swap into {course_name} {section_name}'
    log_str_alt = f'{netid} contacted you about swapping into your section {course_name} {section_name}'
    _db = Database()

    # protects against HTML injection
    if '<' in log_str or '>' in log_str or 'script' in log_str:
        print('HTML code detected in', log_str, file=stderr)
        return jsonify({'isSuccess': False})

    try:
        _db.update_user_trade_log(netid, log_str)
        _db.update_user_trade_log(match_netid, log_str_alt)
    except:
        return jsonify({'isSuccess': False})
    return jsonify({'isSuccess': True})


@app.route('/fill_section/<classid>', methods=['POST'])
def fill_section(classid):
    netid = _CAS.authenticate()
    netid = netid.strip()
    try:
        if not is_admin(netid):
            return redirect(url_for('landing'))
    except:
        return redirect(url_for('landing'))

    try:
        db = Database()
        curr_enrollment = db.get_class_enrollment(classid)
        db.update_enrollment(
            classid, curr_enrollment['capacity'], curr_enrollment['capacity'])
        db._add_admin_log(f'manually filled enrollments for class {classid}')
    except:
        return jsonify({'isSuccess': False})

    return jsonify({'isSuccess': True})

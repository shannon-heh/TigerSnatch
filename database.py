# ----------------------------------------------------------------------
# database.py
# Contains Database, a class used to communicate with the TigerSnatch
# database.
# ----------------------------------------------------------------------

from sys import stdout, stderr
import re
from config import DB_CONNECTION_STR, COLLECTIONS, MAX_LOG_LENGTH, MAX_WAITLIST_SIZE, MAX_ADMIN_LOG_LENGTH, HEROKU_API_KEY
from schema import COURSES_SCHEMA, CLASS_SCHEMA, MAPPINGS_SCHEMA, ENROLLMENTS_SCHEMA
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from datetime import datetime
from os import system
import heroku3


class Database:

    # creates a reference to the TigerSnatch MongoDB database

    def __init__(self):
        print(
            f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}: connecting to database', end='...')
        stdout.flush()
        self._db = MongoClient(DB_CONNECTION_STR,
                               serverSelectionTimeoutMS=5000)

        try:
            self._db.admin.command('ismaster')
        except ConnectionFailure:
            print('failed (server not available)', file=stderr)
            raise Exception('server unavailable')

        print('success')
        self._db = self._db.tigersnatch
        self._check_basic_integrity()

    # prints log and adds log to admin collection to track admin activity
    def _add_admin_log(self, log):
        print(log)
        logs = self._db.admin.find_one({}, {'logs': 1, '_id': 0})['logs']
        log = f"{datetime.now().strftime('%b %d, %Y @ %-I:%M %p')} | {log}"
        logs.insert(0, log)

        if len(logs) > MAX_ADMIN_LOG_LENGTH:
            logs.pop(-1)

        self._db.admin.update_one({}, {'$set': {'logs': logs}})

    # returns 20 most recent admin logs
    def get_admin_logs(self):
        return self._db.admin.find_one({}, {'logs': 1, '_id': 0})

    # returns dictionary with all admin data (excluding logs)
    def get_admin_data(self):
        return self._db.admin.find_one({}, {'logs': 0, '_id': 0})

    # returns dictionary with app-related data
    def get_app_data(self):
        num_users = self._db.users.count_documents({})
        num_users_on_waitlists = self._db.waitlists.count_documents(
            {'waitlists': {'$not': {'$size': 0}}})
        num_courses_in_db = self._db.mappings.count_documents({})
        num_sections_with_waitlists = self._db.waitlists.count_documents({})
        return {
            'num_users': num_users,
            'num_users_on_waitlists': num_users_on_waitlists,
            'num_courses_in_db': num_courses_in_db,
            'num_sections_with_waitlists': num_sections_with_waitlists
        }

    # connects to heroku and returns app variable so you can do operations with heroku
    def connect_to_heroku(self):
        heroku_conn = heroku3.from_key(HEROKU_API_KEY)
        app = heroku_conn.apps()['tigersnatch']
        return app

    # turn Heroku maintenance mode ON (True) or OFF (False)
    def set_maintenance_status(self, status):
        if not isinstance(status, bool):
            raise Exception('status must be a boolean')

        app = self.connect_to_heroku()
        if status:
            app.enable_maintenance_mode()
        else:
            app.disable_maintenance_mode()

        self._add_admin_log(
            f'heroku maintenance mode is now {"on" if status else "off"}')

    # sets notification script status to either True (on) or False (off)

    def set_cron_notification_status(self, status):
        if not isinstance(status, bool):
            raise Exception('status must be a boolean')

        self._add_admin_log(
            f'notification cron script status set to {"on" if status else "off"}')
        cmd = f'heroku ps:scale clock={1 if status else 0}'
        print('executing', cmd, end=' ...')
        stdout.flush()
        system(cmd)
        self._db.admin.update_one({}, {'$set': {'notifications_on': status}})

    # sets notification script status; either True (on) or False (off)

    def get_cron_notification_status(self):
        try:
            return self._db.admin.find_one({})['notifications_on']
        except:
            raise Exception(
                'notifications_on attribute missing', file=stderr)

    # clears and removes users from all waitlists

    def clear_all_waitlists(self):
        self._add_admin_log('clearing waitlists in users collection')
        self._db.users.update_many(
            {},
            {'$set': {'waitlists': []}}
        )

        self._add_admin_log('clearing waitlists in waitlists collection')
        self._db['waitlists'].delete_many({})

    # clears and removes users from the waitlist for class classid

    def clear_class_waitlist(self, classid):
        try:
            class_waitlist = self.get_class_waitlist(classid)['waitlist']
            self._add_admin_log('removing users', class_waitlist,
                                'from class', classid)

            self._db.users.update_many({'netid': {'$in': class_waitlist}},
                                       {'$pull': {'waitlists': classid}})
            self._db.waitlists.delete_one({'classid': classid})
        except:
            self._add_admin_log('waitlist for class', classid,
                                'does not exist - skipping')

    # clears and removes users from all waitlists for class classid

    def clear_course_waitlists(self, courseid):
        try:
            course_data = self.get_course(courseid)
            classids = [i.split('_')[1]
                        for i in course_data.keys() if i.startswith('class_')]
            self._add_admin_log('clearing waitlists for course', courseid)

            for classid in classids:
                self.clear_class_waitlist(classid)
        except:
            self._add_admin_log('failed to clear waitlists for course',
                                courseid, file=stderr)

    # gets current term code from admin collection

    def get_current_term_code(self):
        return self._db.admin.find_one({}, {'current_term_code': 1, '_id': 0})['current_term_code']

    # updates current term code from admin collection

    def update_current_term_code(self, code):
        self._db.admin.update_one({}, {'$set': {'current_term_code': code}})

    # update user netid's log - string must be formatted:
    # "datetime,department_number,section_name,new_slots_count"

    def update_user_log(self, netid, entry):
        user_info = self.get_user(netid)
        log = user_info['log']

        log.insert(0, entry)
        if len(log) > MAX_LOG_LENGTH:
            log.pop(-1)

        self._db.users.update_one({'netid': netid}, {'$set': {'log': log}})
        print(f'log for user {netid} successfully updated with entry {entry}')

    # gets user netid's log in array-of-strings format

    def get_user_log(self, netid):
        return self.get_user(netid)['log']

    # returns user data given netid

    def get_user(self, netid):
        return self._db.users.find_one({'netid': netid.rstrip()})

    # returns all data needed to display user waitlists on dashboard

    def get_dashboard_data(self, netid):
        netid = netid.rstrip()
        dashboard_data = {}
        try:
            waitlists = self._db.users.find_one({'netid': netid})['waitlists']
        except:
            raise RuntimeError(f'user {netid} does not exist')
        for classid in waitlists:
            try:
                class_stats = self.get_class_enrollment(classid)
            except:
                raise RuntimeError(
                    f'classid {classid} not found in enrollments')

            dashboard_data[classid] = {}

            courseid = class_stats['courseid']
            course_data = self.get_course(courseid)
            try:
                class_data = course_data[f'class_{classid}']
            except:
                raise RuntimeError(
                    f'classid {classid} not found in courses')

            dashboard_data[classid]['courseid'] = courseid
            dashboard_data[classid]['displayname'] = course_data['displayname']
            dashboard_data[classid]['section'] = class_data['section']
            dashboard_data[classid]['start_time'] = class_data['start_time']
            dashboard_data[classid]['end_time'] = class_data['end_time']
            dashboard_data[classid]['days'] = class_data['days']
            dashboard_data[classid]['enrollment'] = class_stats['enrollment']
            dashboard_data[classid]['capacity'] = class_stats['capacity']

            try:
                class_waitlist = self._db.waitlists.find_one(
                    {'classid': classid})['waitlist']
                dashboard_data[classid]['position'] = class_waitlist.index(
                    netid)+1
            except ValueError:
                raise ValueError(
                    f'user {netid} not found in waitlist for {classid}')
            except:
                raise RuntimeError(
                    f'classid {classid} not found in waitlists')

        return dashboard_data

        # returns course displayname corresponding to courseid
    def update_user(self, netid, email):
        try:
            self._db.users.update_one({'netid': netid.rstrip()}, {
                '$set': {'email': email}})
        except:
            raise RuntimeError(f'attempt to update email for {netid} failed')

    # returns course displayname corresponding to courseid

    def courseid_to_displayname(self, courseid):
        try:
            displayname = self._db.mappings.find_one(
                {'courseid': courseid})['displayname']
        except:
            raise RuntimeError(f'courseid {courseid} not found in courses')

        return displayname.split('/')[0]

    # returns the corresponding course displayname for a given classid

    def classid_to_course_deptnum(self, classid):
        try:
            courseid = self._db.enrollments.find_one(
                {'classid': classid})['courseid']
        except:
            raise RuntimeError(f'classid {classid} not found in enrollments')

        try:
            displayname = self._db.mappings.find_one(
                {'courseid': courseid})['displayname']
        except:
            raise RuntimeError(f'courseid {courseid} not found in courses')

        return displayname.split('/')[0]

   # returns information about a class including course depts, numbers, title
   # and section number, for display in email/text messages

    def classid_to_classinfo(self, classid):
        try:
            classinfo = self._db.enrollments.find_one(
                {'classid': classid})
            courseid = classinfo['courseid']
            sectionname = classinfo['section']
        except:
            raise Exception(f'classid {classid} cannot be found')

        try:
            mapping = self._db.courses.find_one(
                {'courseid': courseid})
            displayname = mapping['displayname']
            title = mapping['title']
        except:
            raise Exception(f'courseid {courseid} cannot be found')

        dept_num = displayname.split('/')[0]
        return dept_num, title, sectionname

    # returns all classes to which there are waitlisted students

    def get_waited_classes(self):
        return self._db.waitlists.find({}, {'courseid': 1, 'classid': 1, '_id': 0})

    # returns a specific classid's waitlist document

    def get_class_waitlist(self, classid):
        try:
            return self._db.waitlists.find_one({'classid': classid})
        except:
            raise Exception(f'classid {classid} does not exist')

    # returns a specific classid's waitlist size

    def get_class_waitlist_size(self, classid):
        try:
            return len(self.get_class_waitlist(classid)['waitlist'])
        except:
            raise Exception(f'classid {classid} does not exist')

    # checks if user exists in users collection

    def is_user_created(self, netid):
        return self._db.users.find_one({'netid': netid.rstrip()}, {'netid': 1}) is not None

    # creates user entry in users collection

    def create_user(self, netid):
        if self.is_user_created(netid):
            print(f'user {netid} already exists', file=stderr)
            return
        netid = netid.rstrip()
        self._db.users.insert_one(
            {'netid': netid,
             'email': f'{netid}@princeton.edu',
             'phone': '',
             'waitlists': [],
             'log': []})
        print(f'successfully created user {netid}')

    # adds user of given netid to waitlist for class classid

    def add_to_waitlist(self, netid, classid, disable_checks=False):
        # validation checks
        def validate():
            # helper method to check if class is full
            def is_class_full(enrollment_dict):
                return enrollment_dict['enrollment'] >= enrollment_dict['capacity']

            if not self.is_user_created(netid):
                raise Exception(f'user {netid} does not exist')
            class_enrollment = self.get_class_enrollment(classid)
            if class_enrollment is None:
                raise Exception(f'class {classid} does not exist')
            if not is_class_full(class_enrollment):
                raise Exception(
                    f'user cannot enter waitlist for non-full class {classid}')
            if classid in self.get_user(netid)['waitlists']:
                raise Exception(
                    f'user {netid} is already in waitlist for class {classid}')

        netid = netid.rstrip()

        if not disable_checks:
            validate()

        # add classid to user's waitlist
        user_info = self.get_user(netid)
        user_waitlists = user_info['waitlists']
        try:
            if len(user_waitlists) >= MAX_WAITLIST_SIZE:
                print('user', netid, 'exceeded the waitlist limit of',
                      MAX_WAITLIST_SIZE, file=stderr)
                return 0
        except Exception as e:
            print(e, file=stderr)

        user_waitlists.append(classid)
        self._db.users.update_one({'netid': netid}, {
            '$set': {'waitlists': user_waitlists}})

        # add user to waitlist for classid
        waitlist = self.get_class_waitlist(classid)
        if waitlist is None:
            self._db.waitlists.insert_one({'classid': classid, 'waitlist': []})
            class_waitlist = []
        else:
            class_waitlist = waitlist['waitlist']

        class_waitlist.append(netid)
        self._db.waitlists.update_one({'classid': classid}, {
            '$set': {'waitlist': class_waitlist}})

        print(f'user {netid} successfully added to waitlist for class {classid}')
        return 1

    # removes user of given netid to waitlist for class classid
    # if waitlist for class is empty now, delete entry from waitlists collection

    def remove_from_waitlist(self, netid, classid):
        def validate():
            if not self.is_user_created(netid):
                raise Exception(f'user {netid} does not exist')
            waitlist = self.get_class_waitlist(classid)
            if waitlist is None:
                raise Exception(f'no waitlist for class {classid} exists')
            if classid not in self.get_user(netid)['waitlists'] or netid not in waitlist['waitlist']:
                raise Exception(
                    f'user {netid} not in waitlist for class {classid}')

        netid = netid.rstrip()
        validate()

        # remove classid from user's waitlist
        user_info = self.get_user(netid)
        user_waitlists = user_info['waitlists']
        user_waitlists.remove(classid)
        self._db.users.update_one({'netid': netid}, {
            '$set': {'waitlists': user_waitlists}})

        # remove user from waitlist for classid
        class_waitlist = self.get_class_waitlist(classid)['waitlist']
        class_waitlist.remove(netid)
        if len(class_waitlist) == 0:
            self._db.waitlists.delete_one({'classid': classid})
        else:
            self._db.waitlists.update_one({'classid': classid}, {
                '$set': {'waitlist': class_waitlist}})

        print(
            f'user {netid} successfully removed from waitlist for class {classid}')

   # returns list of results whose title and displayname
   # contain user query string

    def search_for_course(self, query):
        query = re.compile(query, re.IGNORECASE)

        res = list(self._db.mappings.find({'$or': [
            {'displayname': {'$regex': query}},
            {'title': {'$regex': query}}
        ]}))

        return res

    # return basic course details for course with given courseid

    def get_course(self, courseid):
        return self._db.courses.find_one(
            {'courseid': courseid}, {'_id': 0})

    # get dictionary for class with given classid in courses
    def get_class(self, courseid, classid):
        try:
            course_data = self.get_course(courseid)
        except:
            raise RuntimeError(f'courseid {courseid} not found in courses')
        try:
            return course_data[f'class_{classid}']
        except:
            raise RuntimeError(f'class {classid} not found in courses')

    # return list of class ids for a course

    def get_classes_in_course(self, courseid):
        classid_list = []
        course_dict = self.get_course(courseid)
        for key in course_dict.keys():
            if key.startswith('class_'):
                classid_list.append(course_dict[key]['classid'])
        return classid_list

    # returns capacity and enrollment for course with given classid

    def get_class_enrollment(self, classid):
        return self._db.enrollments.find_one({'classid': classid}, {'_id': 0})

    # returns dictionary with basic course details AND enrollment,
    # capacity, and boolean isFull field for each class
    # for the given courseid

    def get_course_with_enrollment(self, courseid):
        course_info = self.get_course(courseid)
        for key in course_info.keys():
            if key.startswith('class_'):
                class_dict = course_info[key]
                classid = class_dict['classid']
                class_data = self.get_class_enrollment(classid)
                class_dict['enrollment'] = class_data['enrollment']
                class_dict['capacity'] = class_data['capacity']
                class_dict['isFull'] = (
                    class_dict['capacity'] > 0 and class_dict['enrollment'] >= class_dict['capacity'])
        return course_info

    # updates time that a course page was last updated

    def update_course_time(self, courseid, curr_time):
        try:
            self._db.mappings.update_one({'courseid': courseid}, {
                                         '$set': {'time': curr_time}})
        except:
            raise RuntimeError(f'courseid {courseid} not found in courses')

    # returns time that a course page was last updated
    def get_course_time_updated(self, courseid):
        try:
            time = self._db.mappings.find_one(
                {'courseid': courseid})['time']
        except:
            raise RuntimeError(f'courseid {courseid} not found in courses')
        return time

    # checks if the courses collection contains a course with the
    # passed-in courseid

    def courses_contains_courseid(self, courseid):
        return self._db.courses.find_one({'courseid': courseid}) is not None

    # adds a document containing course data to the courses collection
    # (see Technical Documentation for schema)

    def add_to_courses(self, data):
        def validate(data):
            # validates the keys of the passed-in course data dictionary

            if not all(k in data for k in COURSES_SCHEMA):
                raise RuntimeError('invalid courses document schema')

            for k in data:
                if not k.startswith('class_'):
                    continue
                if not all(k_ in data[k] for k_ in CLASS_SCHEMA):
                    raise RuntimeError(
                        'invalid individual class document schema')

        validate(data)
        self._db.courses.insert_one(data)

    # updates course entry in courses, mappings, and enrollment
    # collections with data dictionary

    def update_course_all(self, courseid, new_course, new_mapping, new_enroll, new_cap):
        def validate(new_course, new_mapping):
            if not all(k in new_course for k in COURSES_SCHEMA):
                raise RuntimeError('invalid courses document schema')

            for k in new_course:
                if not k.startswith('class_'):
                    continue
                if not all(k_ in new_course[k] for k_ in CLASS_SCHEMA):
                    raise RuntimeError(
                        'invalid individual class document schema')

            if not all(k in new_mapping for k in MAPPINGS_SCHEMA):
                raise RuntimeError('invalid mappings document schema')

        validate(new_course, new_mapping)
        self._db.courses.replace_one({'courseid': courseid}, new_course)
        for classid in new_enroll.keys():
            self.update_enrollment(
                classid, new_enroll[classid], new_cap[classid])
        self._db.mappings.replace_one({'courseid': courseid}, new_mapping)

    # adds a document containing mapping data to the mappings collection
    # (see Technical Documentation for schema)

    def add_to_mappings(self, data):
        def validate(data):
            # validates the keys of the passed-in mappings data
            # dictionary

            if not all(k in data for k in MAPPINGS_SCHEMA):
                raise RuntimeError('invalid mappings document schema')

        validate(data)
        self._db.mappings.insert_one(data)

    # adds a document containing enrollment data to the enrollments
    # collection (see Technical Documentation for schema)

    def add_to_enrollments(self, data):
        def validate(data):
            # validates the keys of the passed-in enrollments data
            # dictionary

            if not all(k in data for k in ENROLLMENTS_SCHEMA):
                raise RuntimeError('invalid enrollments document schema')

        validate(data)
        self._db.enrollments.insert_one(data)

    # updates the enrollment and capacity for class classid

    def update_enrollment(self, classid, new_enroll, new_cap):
        self._db.enrollments.update_one({'classid': classid},
                                        {'$set': {'enrollment': new_enroll,
                                                  'capacity': new_cap}})

    # returns list of blacklisted netids
    def get_blacklist(self):
        return self._db.admin.find_one(
            {}, {'blacklist': 1, '_id': 0})['blacklist']

    # returns True if netid is on app blacklist
    def is_blacklisted(self, netid):
        try:
            blacklist = self.get_blacklist()
            return netid in blacklist
        except Exception:
            print(f'error in checking if {netid} is on blacklist', file=stderr)

    # adds netid to app blacklist
    def add_to_blacklist(self, netid):
        # removes user profile from users collection
        # removes user from any waitlists
        def remove_user(netid):
            classids = self._db.users.find_one({'netid': netid})['waitlists']
            for classid in classids:
                self.remove_from_waitlist(netid, classid)
            self._db.users.delete_one({'netid': netid})

        try:
            blacklist = self.get_blacklist()

            # check if user is already in blacklist
            if netid in blacklist:
                self._add_admin_log(
                    f'user {netid} already on app blacklist - not added')
                return

            if self.is_user_created(netid):
                remove_user(netid)

            blacklist.append(netid)
            self._db.admin.update_one(
                {}, {'$set': {'blacklist': blacklist}})
            self._add_admin_log(
                f'user {netid} added to app blacklist and removed from database')

        except Exception:
            print(f'error in adding {netid} to blacklist', file=stderr)

    # remove netid from app blacklist
    def remove_from_blacklist(self, netid):
        try:
            blacklist = self.get_blacklist()
            if netid not in blacklist:
                self._add_admin_log(
                    f'user {netid} is not on app blacklist - not removed')
                return

            blacklist.remove(netid)
            self._db.admin.update_one(
                {}, {'$set': {'blacklist': blacklist}})
            self._add_admin_log(f'user {netid} removed from app blacklist')
        except Exception:
            print(f'Error in removing {netid} from blacklist', file=stderr)

    # does the following:
    #   * clears all "waitlists" lists for each user
    #   * deletes all documents from mappings
    #   * deletes all documents from courses
    #   * deletes all documents from enrollments
    #   * deletes all documents from waitlists
    # NOTE: does not affect user-specific data apart from clearing a
    # user's enrolled waitlists

    def reset_db(self):
        def clear_coll(coll):
            print('clearing', coll)
            self._db[coll].delete_many({})

        print('clearing waitlists in users')
        self._db.users.update_many(
            {},
            {'$set': {'waitlists': []}}
        )

        clear_coll('mappings')
        clear_coll('courses')
        clear_coll('enrollments')
        clear_coll('waitlists')

    # does the following:
    #   * deletes all documents from mappings
    #   * deletes all documents from courses
    #   * deletes all documents from enrollments
    # NOTE: does NOT clear waitlist-related data, unlike self.reset_db()

    def soft_reset_db(self):
        def clear_coll(coll):
            print('clearing', coll)
            self._db[coll].delete_many({})

        clear_coll('mappings')
        clear_coll('courses')
        clear_coll('enrollments')

    # checks that all required collections are available in self._db;
    # raises a RuntimeError if not

    def _check_basic_integrity(self):
        if COLLECTIONS != set(self._db.list_collection_names()):
            raise RuntimeError(
                'one or more database collections is misnamed and/or missing')

    # prints database name, its collections, and the number of documents
    # in each collection

    def __str__(self):
        self._check_basic_integrity()
        ret = f'database {self._db.name} with collections:\n'
        for coll in self._db.list_collection_names():
            ref = self._db[coll]
            ret += f'\t{coll:<15}(#docs: {ref.estimated_document_count()})\n'
        return ret


if __name__ == '__main__':
    db = Database()
    db.add_to_blacklist('ntyp')
    # print(db.get_admin_logs())
    # print(db.get_admin_data())
    # print(db.get_app_data())
    # db.set_maintenance_status(True)
    # db.set_maintenance_status(False)

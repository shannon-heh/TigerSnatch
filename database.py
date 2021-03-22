# ----------------------------------------------------------------------
# database.py
# Contains Database, a class used to communicate with the TigerSnatch
# database.
# ----------------------------------------------------------------------

from sys import exit, stdout, stderr
import re
from config import DB_CONNECTION_STR, COLLECTIONS
from schema import COURSES_SCHEMA, CLASS_SCHEMA, MAPPINGS_SCHEMA, ENROLLMENTS_SCHEMA
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure


class Database:

    # creates a reference to the TigerSnatch MongoDB database

    def __init__(self):
        print('connecting to', DB_CONNECTION_STR, end='...')
        stdout.flush()
        self._db = MongoClient(DB_CONNECTION_STR,
                               serverSelectionTimeoutMS=5000)

        try:
            self._db.admin.command('ismaster')
        except ConnectionFailure:
            print('failed (server not available)')
            exit(1)

        print('success')
        self._db = self._db.tigersnatch
        self._check_basic_integrity()

    # returns user data given netid

    def get_user(self, netid):
        return self._db.users.find_one({'netid': netid.rstrip()})

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
        except Exception as e:
            raise e

        try:
            mapping = self._db.courses.find_one(
                {'courseid': courseid})
            displayname = mapping['displayname']
            title = mapping['title']
        except Exception as e:
            raise e

        dept_num = displayname.split('/')[0]
        return f'{dept_num}: {title}', sectionname

    # returns all classes to which there are waitlisted students

    def get_waited_classes(self):
        return self._db.waitlists.find({}, {'courseid': 1, 'classid': 1, '_id': 0})

    # returns a specific classid's waitlist document

    def get_class_waitlist(self, classid):
        return self._db.waitlists.find_one({'classid': classid})

    # checks if user exists in users collection

    def is_user_created(self, netid):
        return self.get_user(netid) is not None

    # creates user entry in users collection

    def create_user(self, netid):
        if self.is_user_created(netid):
            print(f'user {netid} already exists', file=stderr)
            return
        netid = netid.rstrip()
        self._db.users.insert_one(
            {'netid': netid, 'email': f'{netid}@princeton.edu', 'phone': '', 'waitlists': []})
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

        if len(res) == 0:
            return None
        return res

    # return basic course details for course with given courseid

    def get_course(self, courseid):
        return self._db.courses.find_one(
            {'courseid': courseid}, {'_id': False})

    # return list of class ids for a course

    def get_classes_in_course(self, courseid):
        classid_list = []
        course_dict = self.get_course(courseid)
        for key in course_dict.keys():
            if key.startswith('class_'):
                classid_list.append(course_dict[key]['classid'])
        return classid_list

    # returns capacity and enrollment for course with given courseid

    def get_class_enrollment(self, classid):
        return self._db.enrollments.find_one({'classid': classid}, {'_id': False})

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
        self._db.courses.replace_one({"courseid": courseid}, new_course)
        for classid in new_enroll.keys():
            self.update_enrollment(
                classid, new_enroll[classid], new_cap[classid])
        self._db.mappings.replace_one({"courseid": courseid}, new_mapping)

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
    # print(db)
    db.reset_db()
    # print(db.classid_to_course_deptnum('41021'))
    # print(list(db.get_waited_classes()))

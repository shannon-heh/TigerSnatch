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
                               serverSelectionTimeoutMS=2000)

        try:
            self._db.admin.command('ismaster')
        except ConnectionFailure:
            print('failed (server not available)')
            exit(1)

        print('success')
        self._db = self._db.tigersnatch
        self._check_basic_integrity()

    # helper method to check if class is full
    def is_class_full(self, enrollment_dict):
        return enrollment_dict['enrollment'] == enrollment_dict['capacity']

    # returns user data given netid
    def get_user(self, netid):
        return self._db.users.find_one({"netid": netid.rstrip()})

    # returns the corresponding course displayname for a given classid
    def classid_to_course_deptnum(self, classid):
        try:
            courseid = self._db.enrollments.find_one(
                {"classid": classid})['courseid']
        except:
            raise RuntimeError(f'classid {classid} not found in enrollments')

        try:
            displayname = self._db.courses.find_one(
                {"courseid": courseid})['displayname']
        except:
            raise RuntimeError(f'courseid {courseid} not found in courses')

        return displayname.split('/')[0]

    def get_waited_classes(self):
        return self._db.waitlists.find({}, {"courseid": 1, "classid": 1, "_id": 0})

    def get_class_enrollment(self, classid):
        return self._db.enrollments.find_one({"classid": classid})

    def get_class_waitlist(self, classid):
        return self._db.waitlists.find_one({"classid": classid})

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
            {"netid": netid, "email": f"{netid}@princeton.edu", "phone": "", "waitlists": []})
        print(f'successfully created user {netid}')

    # adds user of given netid to waitlist for class classid
    def add_to_waitlist(self, netid, classid):
        # validation checks
        def validate():
            if not self.is_user_created(netid):
                print(f'user {netid} does not exist', file=stderr)
                return False
            class_enrollment = self.get_class_enrollment(classid)
            if class_enrollment is None:
                print(f'class {classid} does not exist', file=stderr)
                return False
            if not self.is_class_full(class_enrollment):
                print(
                    f'user cannot enter waitlist for non-full class {classid}', file=stderr)
                return False
            if classid in self.get_user(netid)['waitlists']:
                print(
                    f'user {netid} is already in waitlist for class {classid}', file=stderr)
                return False
            return True

        netid = netid.rstrip()
        if not validate():
            return

        # add classid to user's waitlist
        user_info = self.get_user(netid)
        user_waitlists = user_info['waitlists']
        user_waitlists.append(classid)
        self._db.users.update_one({"netid": netid}, {
            "$set": {"waitlists": user_waitlists}})

        # add user to waitlist for classid
        waitlist = self.get_class_waitlist(classid)
        if waitlist is None:
            self._db.waitlists.insert_one({"classid": classid, "waitlist": []})
            class_waitlist = []
        else:
            class_waitlist = waitlist['waitlist']

        class_waitlist.append(netid)
        self._db.waitlists.update_one({"classid": classid}, {
            "$set": {"waitlist": class_waitlist}})

        print(f"user {netid} successfully added to waitlist for class {classid}")

    # removes user of given netid to waitlist for class classid
    # if waitlist for class is empty now, delete entry from waitlists collection

    def remove_from_waitist(self, netid, classid):
        def validate():
            if not self.is_user_created(netid):
                print(f'user {netid} does not exist', file=stderr)
                return False
            waitlist = self.get_class_waitlist(classid)
            if waitlist is None:
                print(f'no waitlist for class {classid} exists')
                return False
            if classid not in self.get_user(netid)['waitlists'] or netid not in waitlist['waitlist']:
                print(
                    f'user {netid} not in waitlist for class {classid}')
                return False
            return True

        netid = netid.rstrip()
        if not validate():
            return

        # remove classid from user's waitlist
        user_info = self.get_user(netid)
        user_waitlists = user_info['waitlists']
        user_waitlists.remove(classid)
        self._db.users.update_one({"netid": netid}, {
            "$set": {"waitlists": user_waitlists}})

        # remove user from waitlist for classid
        class_waitlist = self.get_class_waitlist(classid)['waitlist']
        class_waitlist.remove(netid)
        if len(class_waitlist) == 0:
            self._db.waitlists.delete_one({"classid": classid})
        else:
            self._db.waitlists.update_one({"classid": classid}, {
                "$set": {"waitlist": class_waitlist}})

        print(
            f"user {netid} successfully removed from waitlist for class {classid}")

   # returns list of results whose title and ddisplayname
   # contain user query string

    def search_for_course(self, query):
        query = re.compile(query, re.IGNORECASE)

        res = list(self._db.mappings.find({"$or": [
            {"displayname": {"$regex": query}},
            {"title": {"$regex": query}}
        ]}))

        if len(res) == 0:
            return None
        return res

    # return basic course details for course with given courseid

    def get_course(self, courseid):
        return self._db.courses.find_one(
            {"courseid": courseid}, {"_id": False})

    # returns capacity and enrollment for course with given courseid

    def get_class_enrollment(self, classid):
        return self._db.enrollments.find_one({"classid": classid}, {"_id": False})

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
                    class_dict['capacity'] > 0 and class_dict['enrollment'] == class_dict['capacity'])
        return course_info

    # checks if the courses collection contains a course with the
    # passed-in courseid

    def courses_contains_courseid(self, courseid):
        return self._db.courses.find_one({"courseid": courseid}) is not None

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
    print(db)
    # db.reset_db()
    print(db.classid_to_course_deptnum("41021"))
    print(list(db.get_waited_classes()))

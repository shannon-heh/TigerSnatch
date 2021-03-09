# ----------------------------------------------------------------------
# database.py
# Contains Database, a class used to communicate with the TigerSnatch
# database.
# ----------------------------------------------------------------------

from sys import exit, stdout
import re
from config import DB_CONNECTION_STR, COLLECTIONS
from schema import COURSES_SCHEMA, CLASS_SCHEMA, MAPPINGS_SCHEMA, ENROLLMENTS_SCHEMA
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure


class Database(object):
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
    db.reset_db()
    print(db)

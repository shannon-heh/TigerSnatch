# ----------------------------------------------------------------------
# database.py
# Contains Database, a class used to communicate with the TigerSnatch
# database.
# ----------------------------------------------------------------------

from config import DB_CONNECTION_STR, COLLECTIONS
from schema import COURSES_SCHEMA, CLASS_SCHEMA
from pymongo import MongoClient


class Database(object):
    # creates a reference to the TigerSnatch MongoDB database
    def __init__(self):
        try:
            self._db = MongoClient(DB_CONNECTION_STR).tigersnatch
            print('connected to tigersnatch database at', DB_CONNECTION_STR)
        except:
            print('failed to connect to tigersnatch database')

        self._check_basic_integrity()

    # adds a document containing course data to the courses collection
    # (see Technical Documentation for schema)

    def add_to_courses(self, data):
        def validate(data):
            # validates the keys of the passed-in data dictionary

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

# ----------------------------------------------------------------------
# monitor.py
# Manages enrollment updates through cross-referencing MobileApp and
# the database.
# ----------------------------------------------------------------------

from coursewrapper import CourseWrapper
from database import Database
from mobileapp import MobileApp
from multiprocess import Pool
from os import cpu_count
from time import time
from monitor_utils import get_latest_term, process


class Monitor:
    def __init__(self):
        self._db = Database()
        self._api = MobileApp()

    # organizes all waited-on classes into groups by their parent course

    def _construct_waited_classes(self):
        waited_classes = list(self._db.get_waited_classes())
        data = {}

        for class_ in waited_classes:
            classid = class_['classid']
            deptnum = self._db.classid_to_course_deptnum(classid)

            print('adding classid', classid, 'from', deptnum)

            if deptnum in data:
                data[deptnum].append(classid)
            else:
                data[deptnum] = [classid]

        self._waited_classes = data

    # constructs CourseWrapper objects for all course buckets as
    # specified in _construct_waited_classes()

    def _analyze_classes(self):
        term = get_latest_term()
        process_args = []

        for course, classes in self._waited_classes.items():
            process_args.append([term, course, classes])

        # alleviate MobileApp bottleneck using multiprocessing
        with Pool(cpu_count()) as pool:
            all_data = pool.map(process, process_args)

        self._waited_course_wrappers = all_data

    # generates, caches, and returns a dictionary in the form:
    # {
    #   classid1: n_slots_available,
    #   classid2: n_slots_available,
    #   ...
    # }
    # the result is to be used to determine to whom notifications are to
    # be sent

    def get_classes_with_changed_enrollments(self):
        try:
            return self._changed_enrollments
        except:
            print('cached enrollments data not found; performing analysis')

        tic = time()

        self._construct_waited_classes()
        try:
            self._waited_classes
        except:
            raise RuntimeError('missing _waited_classes')

        self._analyze_classes()
        try:
            self._waited_course_wrappers
        except:
            raise RuntimeError('missing _waited_course_wrappers')

        data = {}
        for course in self._waited_course_wrappers:
            print('generating enrollment delta for',
                  course.get_course_deptnum())

            for class_, n_slots in course.get_available_slots().items():
                data[class_] = n_slots

        self._changed_enrollments = data
        print(f'success: approx. {round(time()-tic)} seconds')
        print('enrollments data has been cached; re-call this method to retrieve the cached version')
        return self._changed_enrollments


if __name__ == '__main__':
    monitor = Monitor()
    print(monitor.get_classes_with_changed_enrollments())
    print('**************************')
    # call again to retrieve cached version
    print(monitor.get_classes_with_changed_enrollments())

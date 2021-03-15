# ----------------------------------------------------------------------
# monitor.py
# Manages enrollment updates through cross-referencing MobileApp and
# the database.
# ----------------------------------------------------------------------

from coursewrapper import CourseWrapper
from database import Database
from mobileapp import MobileApp


class Monitor:
    def __init__(self):
        self._db = Database()
        self._api = MobileApp()

    def _construct_waited_classes(self):
        waited_classes = list(self._db.get_waited_classes())
        data = {}

        for class_ in waited_classes:
            deptnum = self._db.classid_to_course_deptnum(class_['classid'])

            if deptnum in data:
                data[deptnum].append(class_['classid'])
            else:
                data[deptnum] = [class_['classid']]

        return data


if __name__ == '__main__':
    monitor = Monitor()
    print(monitor._construct_waited_classes())

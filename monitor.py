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
        waitlisted_classes = self._db.get_waitlisted_classes()

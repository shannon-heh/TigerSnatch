from database import Database


class Waitlist:

    def __init__(self, netid):
        self._netid = netid
        self._db = Database()

    def add_to_waitlist(self, classid):
        self._db.add_to_waitlist(self._netid, classid)

    def remove_from_waitlist(self, classid):

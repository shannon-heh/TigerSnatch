# ----------------------------------------------------------------------
# $exec_notifs.py
# Script that wraps core email notification logic - designed to be run
# on a regular interval.
# ----------------------------------------------------------------------

from notify import Notify
from monitor import Monitor
from database import Database

if __name__ == '__main__':
    monitor = Monitor()
    db = Database()

    # get all class openings (for waited-on classes) from MobileApp
    new_slots = monitor.get_classes_with_changed_enrollments()

    for classid, n_new_slots in new_slots.items():
        for i in range(min(db.get_class_waitlist_size(classid), n_new_slots)):
            try:
                notify = Notify(classid)
                notify.send_email_html()
                db.remove_from_waitlist(notify.get_netid(), classid)
            except Exception as e:
                print(e)

                # for i in range(min(size_of_waitlist(classid), new_slots[classid]))

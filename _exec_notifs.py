# ----------------------------------------------------------------------
# _exec_notifs.py
# Script that wraps core email notification logic - designed to be run
# on a regular interval.
# ----------------------------------------------------------------------

from notify import Notify
from monitor import Monitor
from database import Database
from sys import stdout
from time import time

if __name__ == '__main__':
    tic = time()
    monitor = Monitor()
    db = Database()

    # get all class openings (for waited-on classes) from MobileApp
    new_slots = monitor.get_classes_with_changed_enrollments()

    total = 0
    for classid, n_new_slots in new_slots.items():
        n_notifs = min(db.get_class_waitlist_size(classid), n_new_slots)

        for i in range(n_notifs):
            try:
                notify = Notify(classid)

                print(notify)
                print('sending email to', notify.get_netid(), end='...')
                stdout.flush()

                # only if email was sent, remove user from waitlist
                if notify.send_email_html():
                    print('success')
                    print(i+1, '/', n_notifs, 'emails sent for this class')
                    total += 1
                    db.remove_from_waitlist(notify.get_netid(), classid)
                else:
                    print('failed to send email')
            except Exception as e:
                print(e)

    print('done: sent a total of', total,
          'emails in approx.', round(time()-tic), 'seconds')

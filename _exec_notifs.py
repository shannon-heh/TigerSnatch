# ----------------------------------------------------------------------
# _exec_notifs.py
# Script that wraps core email notification logic - designed to be run
# on a regular interval.
#
# Approximate execution frequency: 2-5 minutes after the previous
# execution completion. The script itself can take a minute or two to
# run, depending on the number of waited-on classes.
#
# Example: python _exec_notifs.py
# ----------------------------------------------------------------------

from notify import Notify
from monitor import Monitor
from database import Database
from sys import stdout, stderr
from time import time
from datetime import datetime

if __name__ == '__main__':
    tic = time()
    monitor = Monitor()
    db = Database()

    print(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    # get all class openings (for waited-on classes) from MobileApp
    new_slots = monitor.get_classes_with_changed_enrollments()

    total = 0
    for classid, n_new_slots in new_slots.items():
        try:
            # n_notifs = min(db.get_class_waitlist_size(classid), n_new_slots)
            n_notifs = db.get_class_waitlist_size(classid)
        except Exception as e:
            print(e, file=stderr)
            continue

        for i in range(n_notifs):
            try:
                notify = Notify(classid, i)

                print(notify)
                print('sending email to', notify.get_netid(), end='...')
                stdout.flush()

                # only if email was sent, remove user from waitlist
                if notify.send_email_html():
                    print('success')
                    print(i+1, '/', n_notifs, 'emails sent for this class')
                    total += 1
                    # db.remove_from_waitlist(notify.get_netid(), classid)
                else:
                    print('failed to send email')
            except Exception as e:
                print(e, file=stderr)

            print()

    print('done: sent a total of', total,
          'emails in approx.', round(time()-tic), 'seconds')

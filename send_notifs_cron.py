# ----------------------------------------------------------------------
# send_notifs_cron.py
# Manages regular execution of the email notification script using a
# cron wrapper. Disable/enable using admin panel or _set_cron_status.py.
#
# Set execution interval in config:     NOTIFS_INTERVAL_SECS
# ----------------------------------------------------------------------

from sys import path
path.append('src')  # noqa

from send_notifs import cronjob
from config import NOTIFS_INTERVAL_SECS
from apscheduler.schedulers.blocking import BlockingScheduler


scheduler = BlockingScheduler()
scheduler.add_job(cronjob, 'interval', seconds=NOTIFS_INTERVAL_SECS)

scheduler.start()

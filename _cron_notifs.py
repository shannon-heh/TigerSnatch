# ----------------------------------------------------------------------
# cron_notifs.py
# Manages regular execution of the email notification script using a
# cron wrapper.
#
# Enable with:                          heroku ps:scale clock=1
# Disable with:                         heroku ps:scale clock=0
# Set execution interval in config:     NOTIFS_INTERVAL_MINS
# ----------------------------------------------------------------------

from send_notifs import cronjob
from config import NOTIFS_INTERVAL_MINS
from apscheduler.schedulers.blocking import BlockingScheduler


scheduler = BlockingScheduler()
scheduler.add_job(cronjob, 'interval', minutes=NOTIFS_INTERVAL_MINS)

scheduler.start()

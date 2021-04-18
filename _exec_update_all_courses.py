# ----------------------------------------------------------------------
# _exec_update_all_courses.py
# Resets and updates the TigerSnatch database with courses from the
# latest term.
#
# Specify one of the following flags:
#   --soft: resets only course-related data
#	--hard: resets both course and waitlist-related data
#
# Approximate execution frequency: once at the start of every course
# selection period i.e. on or after (asap) the date when courses for the
# next semester are released on the Registrar's Course Offerings
# website.
#
# WARNING: all waitlist-related data will be CLEARED if the flag --hard
# is specified. We recommend running this script with --hard only ONCE
# at the very beginning of the course selection period. If you wish to
# refresh only course (non-waitlist) data, run with --soft (this may be
# run safely throughout the semester, but that is not recommended unless
# there are MAJOR changes to the semester's course offerings).
#
# Example: python _exec_update_all_courses.py --soft
# ----------------------------------------------------------------------

from mobileapp import MobileApp
from database import Database
from sys import argv, exit
from time import time
from update_all_courses_utils import get_all_dept_codes, process_dept_code

if __name__ == '__main__':
    def process_args():
        if len(argv) != 2 or (argv[1] != '--soft' and argv[1] != '--hard'):
            print('specify one of the following flags:')
            print('\t--soft: resets only course-related data')
            print('\t--hard: resets both course and waitlist-related data')
            exit(2)
        return argv[1] == '--hard'

    tic = time()
    hard_reset = process_args()
    db = Database()
    db.set_maintenance_status(True)

    notifs_were_on = db.get_cron_notification_status()
    if notifs_were_on:
        db.set_cron_notification_status(False)

    # get current term code
    terms = MobileApp().get_terms()

    try:
        current_term_code = terms['term'][0]['code']
        db.update_current_term_code(current_term_code)
        ######################### REMOVE LATER #########################
        # current_term_code = '1214'
        # db.update_current_term_code('1214')
        ################################################################
    except:
        raise Exception('failed to get current term code')

    print(f'getting all courses in term code {current_term_code}')

    DEPT_CODES = get_all_dept_codes(current_term_code)

    process_dept_code_args = []
    for n, code in enumerate(DEPT_CODES):
        process_dept_code([code, n, current_term_code, False, hard_reset])
        # the below code is for multiprocessing
        # process_dept_code_args.append(
        #     [code, n, current_term_code, True, hard_reset])

    # alleviate MobileApp bottleneck using multiprocessing
    # NOTE: setting cores to > 1 yields in different results every time
    # replace with cpu_count() if someone figures out why - it's not a
    # big issue though because this script is run only once per semester

    # with Pool(1) as pool:
    #     pool.map(process_dept_code, process_dept_code_args)

    db.set_maintenance_status(False)

    if notifs_were_on:
        db.set_cron_notification_status(True)

    db._add_admin_log(
        f'updated courses to term code {current_term_code} in {round(time()-tic)} seconds')

    print(f'success: approx. {round(time()-tic)} seconds')

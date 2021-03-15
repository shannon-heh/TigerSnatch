# ----------------------------------------------------------------------
# update_all_courses.py
# Resets and updates the TigerSnatch database with courses from the
# latest term, clearing all waitlists and waitlist student enrollments.
# ----------------------------------------------------------------------

from sys import exit
from time import time
from multiprocess import Pool
from os import cpu_count
from mobileapp import MobileApp
from update_all_courses_utils import get_all_dept_codes, process_dept_code

if __name__ == '__main__':
    tic = time()
    terms = MobileApp().get_terms()

    try:
        current_term_code = terms['term'][0]['code']
        current_term_date = terms['term'][0]['suffix']
    except:
        print('failed to get current term code')
        exit(1)

    print(
        f'getting all courses in {current_term_date} (term code {current_term_code})')

    DEPT_CODES = get_all_dept_codes(current_term_code)

    process_dept_code_args = []
    for n, code in enumerate(DEPT_CODES):
        process_dept_code_args.append([code, n, current_term_code, True])

    # alleviate MobileApp bottleneck using multiprocessing
    # NOTE: setting cores to > 1 yields in different results every time
    # replace with cpu_count() if someone figures out why - it's not a
    # big issue though because this script is run only once per semester
    with Pool(1) as pool:
        pool.map(process_dept_code, process_dept_code_args)

    print(f'success: approx. {round(time()-tic)} seconds')

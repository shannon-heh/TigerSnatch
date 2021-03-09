# ----------------------------------------------------------------------
# update_enrollments.py
# Resets and updates the TigerSnatch database with courses from the
# latest term, clearing all waitlists and waitlist student enrollments.
# ----------------------------------------------------------------------

from mobileapp import MobileApp
from database import Database
from schema import DEPT_CODES

if __name__ == '__main__':
    def process_dept_code(code, db, api, n):
        print('processing dept code', code)
        courses = api.getJSON(
            api.configs.COURSE_COURSES,
            fmt='json',
            term=current_term_code,
            subject=code
        )

        if 'subjects' not in courses['term'][0]:
            raise RuntimeError('no query results')

        if n == 0:
            db.reset_db()

        for subject in courses['term'][0]['subjects']:
            for course in subject['courses']:
                courseid = course['course_id']
                if db.courses_contains_courseid(courseid):
                    print('already processed courseid', courseid, '- skipping')
                    continue

                # "new" will contain a single course document to be entered
                # in the courses (and, in part, the mapppings) collection
                new = {
                    'courseid': courseid,
                    'displayname': subject['code'] + course['catalog_number'],
                    'title': course['title']
                }

                for x in course['crosslistings']:
                    new['displayname'] += '/' + \
                        x['subject'] + x['catalog_number']

                print('inserting', new['displayname'], 'into mappings')
                db.add_to_mappings(new)

                for i, class_ in enumerate(course['classes']):
                    meetings = class_['schedule']['meetings'][0]

                    # new_class will contain a single lecture, precept, etc.
                    # for a given course
                    new_class = {
                        'classid': class_['class_number'],
                        'section': class_['section'],
                        'type_name': class_['type_name'],
                        'start_time': meetings['start_time'],
                        'end_time': meetings['end_time'],
                        'days': ' '.join(meetings['days'])
                    }

                    new_class_enrollment = {
                        'classid': class_['class_number'],
                        'enrollment': int(class_['enrollment']),
                        'capacity': int(class_['capacity'])
                    }

                    print('inserting', new['displayname'],
                          new_class['section'], 'into enrollments')
                    db.add_to_enrollments(new_class_enrollment)

                    if new_class['start_time'] == '01:00 AM':
                        new_class['start_time'] = 'Pre-Recorded'
                        new_class['end_time'] = ''

                    new[f'class_{i}'] = new_class

                print('inserting', new['displayname'], 'into courses')
                db.add_to_courses(new)

        print()

    db = Database()

    api = MobileApp()
    term = api.getJSON(
        api.configs.COURSE_TERMS,
        fmt='json'
    )

    current_term_code = term['term'][0]['code']
    current_term_date = term['term'][0]['suffix']
    print(
        f'getting all courses in {current_term_date} (term code {current_term_code})')

    for n, code in enumerate(DEPT_CODES):
        process_dept_code(code, db, api, n)

    print('success')

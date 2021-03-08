# ----------------------------------------------------------------------
# update_enrollments.py
# Resets and updates the TigerSnatch database with courses from the
# latest term, clearing all waitlists and waitlist student enrollments.
# ----------------------------------------------------------------------

from mobileapp import MobileApp
from database import Database

if __name__ == '__main__':
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

    courses = api.getJSON(
        api.configs.COURSE_COURSES,
        fmt='json',
        term=current_term_code,
        subject='ECO'
    )

    if 'subjects' not in courses['term'][0]:
        raise RuntimeError('no query results')

    db.reset_db()

    for subject in courses['term'][0]['subjects']:
        for course in subject['courses']:
            new = {
                'courseid': course['course_id'],
                'displayname': subject['code'] + course['catalog_number'],
                'title': course['title']
            }

            for x in course['crosslistings']:
                new['displayname'] += '/' + x['subject'] + x['catalog_number']

            for i, class_ in enumerate(course['classes']):
                meetings = class_['schedule']['meetings'][0]
                new_class = {
                    'classid': class_['class_number'],
                    'section': class_['section'],
                    'type_name': class_['type_name'],
                    'start_time': meetings['start_time'],
                    'end_time': meetings['end_time'],
                    'days': ' '.join(meetings['days'])
                }

                if new_class['start_time'] == '01:00 AM':
                    new_class['start_time'] = 'Pre-Recorded'
                    new_class['end_time'] = ''

                new[f'class_{i}'] = new_class

            print('inserting', new['displayname'])
            db.add_to_courses(new)

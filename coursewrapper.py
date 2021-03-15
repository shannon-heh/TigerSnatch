# ----------------------------------------------------------------------
# coursewrapper.py
# Helper class for Monitor, mainly used to compute available slots for
# all classes in course courseid.
# ----------------------------------------------------------------------

class CourseWrapper:
    def __init__(self, courseid, new_enroll, new_cap):
        self._courseid = courseid
        self._new_enroll = new_enroll
        self._new_cap = new_cap
        self._compute_available_slots()

    # returns courseid

    def get_courseid(self):
        return self._courseid

    # returns dictionary containing available slots for all inputted
    # classids

    def get_available_slots(self):
        try:
            return self._available_slots
        except:
            raise RuntimeError('available slots have not yet been calculated')

    # computes available slots for all classids

    def _compute_available_slots(self):
        diff = {}

        for k in self._new_enroll:
            try:
                d = self._new_cap[k] - self._new_enroll[k]
            except:
                raise RuntimeError(
                    f'missing key {k} in either new_cap or new_enroll')

            diff[k] = max(d, 0)

        self._available_slots = diff

    # string representation; prints courseid, classids, and all
    # associated available slot counts

    def __str__(self):
        ret = f'CourseWrapper for courseid {self._courseid}:\n'

        for k, v in self._available_slots.items():
            ret += f'\tclassid {k}: {v} available slot(s)\n'

        return ret


if __name__ == '__main__':
    new_enroll = {
        '1': 9,
        '2': 10,
        '3': 11
    }

    new_cap = {
        '1': 10,
        '2': 10,
        '3': 10
    }

    course = CourseWrapper('01234', new_enroll, new_cap)

    print(course)
    print(course.get_available_slots())
    print(course.get_courseid())

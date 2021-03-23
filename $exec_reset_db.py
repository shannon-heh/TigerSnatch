# ----------------------------------------------------------------------
# $exec_reset_db.py
# Simple script to either soft or hard reset the database.
# ----------------------------------------------------------------------

from database import Database
from sys import exit

print('Database reset options')
print('----------------------')
print('1: SOFT reset (clears only course-related data)')
print('2: HARD reset (clears course-related AND waitlist-related data)')
print('3: never mind!')

try:
    action = int(input('Type a number and press enter: '))
except:
    print('non-integer inputted')
    exit(1)

if action == 1:
    database = Database()
    database.soft_reset_db()
    print('done')
elif action == 2:
    database = Database()
    database.reset_db()
    print('done')
elif action == 3:
    exit(0)
else:
    print('invalid action inputted')

# ----------------------------------------------------------------------
# _set_maintenance_mode.py
# Simple script to enable or disable the cron notification script.
#
# Specify one of the following flags:
#   --on: Enables maintenance mode.
#	--off: Disables maintenance mode.
#
# Example: python _set_maintenance_mode.py --on
# ----------------------------------------------------------------------

from sys import exit, argv
from database import Database

if __name__ == '__main__':
    def process_args():
        if len(argv) != 2 or (argv[1] != '--on' and argv[1] != '--off'):
            print('specify one of the following flags:')
            print('\t--on: enable maintenance mode')
            print('\t--off: disable maintenance mode')
            exit(2)
        return argv[1] == '--on'

    turn_on = process_args()

    Database().set_maintenance_status(turn_on)
    print('done')

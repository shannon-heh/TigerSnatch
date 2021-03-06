#!/usr/bin/env python

#-----------------------------------------------------------------------
# runserver.py
# Author: Bob Dondero
#-----------------------------------------------------------------------

from sys import argv, exit, stderr
from penny import app

def main(argv):

    if len(argv) != 2:
        print('Usage: ' + argv[0] + ' port', file=stderr)
        exit(1)
    
    try:
        port = int(argv[1])
    except Exception:
        print('Port must be an integer.', file=stderr)
        exit(1)
        
    app.run(host='0.0.0.0', port=port, debug=True)

if __name__ == '__main__':
    main(argv)
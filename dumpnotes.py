"""Dump the notes from data files"""

import sys
import h5py as h5
from get_files_by_ts import get_files_by_ts

if __name__ == '__main__':
    if len(sys.argv) != 4:
        print 'Usage: %s directory startdate enddate' % (sys.argv[0])
        sys.exit(1)
    directory = sys.argv[1]
    start = sys.argv[2]
    end = sys.argv[3]        
    filenames = get_files_by_ts(directory, start=start,end= end)
    for f in filenames:
        fd = h5.File(f, 'r')
        notes = fd.attrs['notes'].replace('\n', ' ')
        print '%s\t%s' % (f, notes)
    
    

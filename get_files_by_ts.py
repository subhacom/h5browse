#!/usr/bin/env python

import sys
import h5py as h5
import os
import subprocess
from datetime import datetime

def find_files(path, *args):
    """Use gnu find command to get files in directory `path`. 
    `args` are string arguments to be passed to `find`
    """
    po = subprocess.Popen(['find', path] + list(args), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = po.communicate()
    filenames = [fname for fname in out.split('\n') if fname.strip() ]
    return filenames


filenames = find_files('/data/subha/rsync_ghevar_cortical_data_clone', '-iname', 'data_*.h5')


def get_fname_timestamps(filepaths, start='19700101', end='30000000'):
    """Get a list of 2-tuples of (filename, timestamp) for specified
    files where timestamp is datetime objects lying within [start,
    end] dates.
    
    filepaths: list of file paths

    start: starting date in 'YYYYmmdd' format

    end: end date in 'YYYYmmdd' format
    """
    ret = []
    start = datetime.strptime(start, '%Y%m%d')
    end = datetime.strptime(end, '%Y%m%d')
    for fname in filepaths:
        try:
            fd = h5.File(fname, 'r')
        except IOError, e:
            print 'Error opening:', fname
            print e
            continue
        ts_present = True
        ts = ''
        tmpts = None
        try: # Handle any case when the time stamp attribute was not incorporated
            ts = fd.attrs['timestamp']
        except KeyError, e:
            ts_present = False
            print '%s: %s\n' % (fname, e)
        try: # Many files have the time stamp wrongly formatted
            ts = datetime.strptime(ts, '%Y-%m-%d %H:%M:%S')
        except ValueError, e:
            print '%s: %s\n' % (fname, e)
            ts_present = False
        try:
            tmpts = fname.rpartition('/')[-1] # Get only the filename without parent dir
            tmpts = tmpts.replace('data_', '').replace('.h5', '') # file names are of format `data_YYYYmmdd_HHMMSS_PID.h5`
            tmpts = tmpts.rpartition('_')[0]            
            tmpts = datetime.strptime(tmpts, '%Y%m%d_%H%M%S')      
        except Exception as e:
            print 'Error getting timestamp from filename:', fname
            print '%s: %s\n' % (fname, e)
            tmpts = datetime.strptime('19700101', '%Y%m%d')
        if not ts_present:
            ts = tmpts
        if ts != tmpts:
            print 'File name and timestamp inside file do not match', fname
        if ts >= start and ts <= end:
            ret.append((fname, ts))
        fd.close()
    return ret

# This is the list of current filename, timestamp pairs
current_fts = get_fname_timestamps(filenames, '20120601', '20121201')

# We'll store the file (descriptor, timestamp)  in fdts
fdts = []

for v in current_fts:
    try:
        fd = h5.File(v[0], 'r')
        fdts.append((fd, v[1]))
    except IOError, e:
        print 'Error accessing file %s: %s' % (v[0], e)







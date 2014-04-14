#!/usr/bin/env python

from collections import namedtuple, defaultdict
import sys
import h5py as h5
import os
import subprocess
from datetime import datetime
from operator import itemgetter
import numpy as np
import csv

from traubdata import cellcount_tuple

def find_files(path, *args):
    """Use gnu find command to get files in directory `path`. 
    `args` are string arguments to be passed to `find`
    """
    po = subprocess.Popen(['find', path] + list(args), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = po.communicate()
    filenames = [fname for fname in out.split('\n') if fname.strip() ]
    return filenames

def get_files_by_ts(directory, namepattern='data*h5', start='19700101', end='30001231'):
    startdate = datetime.strptime(start, '%Y%m%d')
    enddate = datetime.strptime(end, '%Y%m%d')
    current = datetime.now()
    startdays = current - startdate
    args = ['find', directory, 
            '-name', namepattern, 
            '-mmin',
            '-%d' % (startdays.days*1440),
            ]
    if current > enddate:
        enddays = current - enddate
        args += ['-mmin', '+%d' % (enddays.days*1440)]

    print args
    po = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = po.communicate()
    filenames = [fname for fname in out.split('\n') if fname.strip()]
    return filenames
    

def get_fname_timestamps(filepaths, start='19700101', end='30001231'):
    """Get a dict of (filename, timestamp) for specified
    files where timestamp is datetime objects lying within [start,
    end] dates.
    
    filepaths: list of file paths

    start: starting date in 'YYYYmmdd' format

    end: end date in 'YYYYmmdd' format
    """
    ret = {}
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
            ret[fname] = ts
        fd.close()
    return ret


def classify_files_by_cellcount(filelist):
    """Categorise files by cell count.

    Return a dict containing cellcount->set of files with that
    cellcount.
    
    """
    categories = defaultdict(set)
    for filename in filelist:
        try:
            with h5.File(filename, 'r') as fd:
                cc = {}
                try:
                    cc = dict([(k, int(v)) for k, v in np.asarray(fd['/runconfig/cellcount'])])        
                    cctuple = cellcount_tuple(**cc)
                    categories[cctuple].add(filename)
                except KeyError, e:
                    print fd.filename, e     
                except TypeError, e1:
                    print fd.filename, e1
                finally:
                    fd.close()
        except (IOError) as e:
            print filename, e
    return categories

def load_spike_data(fnames):
    """Load the spike time data from multiple files into a dictionary
    of dictionaries. Each entry is of the form
    data[filename][cellname] = spiketime_array

    """
    data = {}
    for fn in fnames:
        data[fn] = {}
        fd = None
        try:
            fd = h5.File(fn, 'r')
            for cellname in fd['spikes']:
                data[fn][cellname] = np.asarray(fd['spikes'][cellname])
        finally:
            if fd:
                fd.close()
    return data

def get_simtime(files):
    data = {}
    for fn in files:
        data[fn] = {}
        fd = None
        try:
            fd = h5.File(fn, 'r')
            data[fn] = float(dict(fd['/runconfig/scheduling'])['simtime'])
        except (IOError, KeyError) as e:
            print fn, e
        finally:
            if fd:
                fd.close()
    return data
    

def load_stim_data(files):
    data = {}
    for fn in files:
        fd = None
        try:
            fd = h5.File(fn, 'r')
            data[fn] = (np.asarray(fd['/stimulus/stim_bg']), np.asarray(fd['/stimulus/stim_probe']))
        finally:
            if fd:
                fd.close()
    return data

def get_notes_from_files(filelist):
    """Retrieve the notes for files in file list. Return a dict
    mapping file name to notes."""
    notes = {}
    for fname in filelist:
        fd = None
        try:
            fd = h5.File(fname, 'r')
            notes[fname] = fd.attrs['notes']            
        except IOError, e:
            print 'Error accessing file %s: %s' % (fname, e)
        except KeyError, e1:
            print 'No `notes` attribute in', fname
        finally:
            if fd:
                fd.close()
    return notes

def get_file_info(directory, startdate, enddate=None, outfile='datafileinfo.csv'):
    if enddate is None:
        enddate = datetime.now().strftime('%Y%m%d')
    finfo = namedtuple('fileinfo', ['timestamp', 'name', 'simtime', 'syn_distr', 'sd_ampa', 'sd_gaba', 'sd_nmda', 'sd_Em', 'DeepBasket', 'DeepLTS', 'SpinyStellate', 'DeepAxoaxonic', 'TCR', 'SupPyrRS', 'SupPyrFRB', 'SupLTS', 'SupBasket', 'SupAxoaxonic', 'TuftedIB', 'TuftedRS', 'NontuftedRS', 'nRT'])
    finfo_list = []
    for fname in get_files_by_ts(directory, namepattern='data*h5', start=startdate, end=enddate):
        try:
            with h5.File(fname, 'r') as fd:
                info = dict([(key, 'NA') for key in finfo._fields])
                
                info['timestamp'] = fd.attrs['timestamp']
                info['name'] = fname.split('/')[-1]
                try:
                    runconfig = fd['/runconfig']
                except KeyError:
                    print '"%s" no runconfig' % (fname)
                    continue
                
                try:
                    info['simtime'] = dict(runconfig['scheduling'])['simtime']
                except KeyError:
                    print fname, 'does not have simtime.'
                try:
                    info['syn_distr'] = dict(runconfig['synapse'])['distr']
                except KeyError:
                    pass
                try:
                    info['sd_ampa'] = dict(runconfig['AMPA'])['sd']
                except KeyError:
                    pass
                try:
                    info['sd_nmda'] = dict(runconfig['NMDA'])['sd']
                except KeyError:
                    pass
                try:
                    info['sd_gaba'] = dict(runconfig['GABA'])['sd']
                except KeyError:
                    pass
                try:
                    info['sd_Em'] = dict(runconfig['sd_passive'])['Em']
                except KeyError:
                    pass
                for key, value in runconfig['cellcount']:
                    info[key] = value
                # print fname
                # print info
                try:
                    finfo_list.append(finfo(**info))
                except Exception, e1:
                    print 'Encountered an exception processing "%s":' % (fname)
                    print 'Exceotion:', e1
                    
        except IOError, e:
            print '%s could not be opened for reading.' % (fname)
            print 'Exception:', e
    with open(outfile, 'w') as outfile:
        writer = csv.writer(outfile, delimiter='\t', quotechar='"', quoting=csv.QUOTE_ALL)
        writer.writerow(finfo._fields)
        for info in finfo_list:
            writer.writerow(info)
    return finfo_list
        
        

if __name__ == '__main__':
    # filenames = find_files('/data/subha/rsync_ghevar_cortical_data_clone', '-iname', 'data_*.h5')
    # # This is the list of current filename, timestamp pairs
    # current_fts = get_fname_timestamps(filenames, '20120101', '20140101').items()
    # current_fts = sorted(current_fts, key=itemgetter(1))
    # # We'll store the file (descriptor, timestamp)  in fdts
    # fdts = []

    # for v in current_fts:
    #     print v,
    #     try:
    #         fd = h5.File(v[0], 'r')
    #         fdts.append((fd, v[1]))
    #         print 'opened'
    #     except IOError, e:
    #         print 'Error accessing file %s: %s' % (v[0], e)
    # print '=== printing filenames and notes ==='
    # for f, t in fdts:
    #     print 'notes: "%s" "%s"' % (os.path.basename(f.filename), ' '.join(f.attrs['notes'].split('\n')))
    #     f.close()
    # classify_files_by_cellcount([item[0] for item in current_fts])
    get_file_info('/data/subha/rsync_ghevar_cortical_data_clone',
                  startdate='20120101')

    


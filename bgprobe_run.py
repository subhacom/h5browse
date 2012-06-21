# bgprobe_run.py --- 
# 
# Filename: bgprobe_run.py
# Description: 
# Author: 
# Maintainer: 
# Created: Fri Jun 15 14:40:53 2012 (+0530)
# Version: 
# Last-Updated: Thu Jun 21 09:48:22 2012 (+0530)
#           By: subha
#     Update #: 544
# URL: 
# Keywords: 
# Compatibility: 
# 
# 

# Commentary: 
# 
# 
# 
# 

# Change log:
# 
# 
# 
# 

# Code:

import matplotlib.pyplot as plt
import datetime
from mpl_toolkits.mplot3d import Axes3D
from bgprobe import *

if __name__ == '__main__':
    # First, exclude files older than a cutoff date or simulations which lasted less than 5 s
    # candidate_fh = get_valid_files_handles('/data/subha/rsync_ghevar_cortical_data_clone/')
    candidate_fh = get_valid_files_handles('/data/subha/rsync_ghevar_cortical_data_clone/2012_03_09/')
    cutoff_date = datetime.datetime(2012, 01, 01)
    good_fh = []    
    for fh in candidate_fh:
        token = fh.filename.split('_')
        date = datetime.datetime.strptime(token[-3], '%Y%m%d')
        simtime = float(dict(fh['runconfig/scheduling'])['simtime'])
        if (date < cutoff_date) or (simtime < 5.0):
            fh.close()
        else:
            good_fh.append(fh)
    # Now categorize these files according to network types
    cats = categorise_networks(good_fh)
    celltypes = ['SpinyStellate']
    markers = {'SpinyStellate': 'p'}
    # Now go through all the files and dump some statistics for each interesting cell type
    dump = h5.File('stats_%s.h5' % (datetime.datetime.now().strftime('%Y%m%d_%H%M%s')), 'w')
    tfs_label = 'Time to first spike'
    tps_label = 'Time of peak spiking'
    fps_label  = 'Peak spiking rate'
    favg_label = 'Average spiking rate'
    for seed, values in cats.items():
        for hash_, files in values.items():
            print '#### processing', seed, hash_
            print '#### Files ####'
            for f in files:
                print f.filename
            cellcount = dict(files[0]['/runconfig/cellcount'])
            isi = float(dict(files[0]['/runconfig/stimulus'])['bg_interval'])
            print '#### cell count ####'
            for cell, count in cellcount.items():
                if int(count) > 0:
                    print cell, count
            # Keep track of the probed cells to highlight them in the plots
            probed_cells = get_probed_cells(files[0])
            probed_cells = [cell for cell in probed_cells for celltype in celltypes if cell.startswith(celltype) ]
            bgdata, probedata, = collect_statistics(files, celltypes)
            assert(set(bgdata.keys()) == set(probedata.keys()))
            fig = plt.figure()
            # t_first_spike - t_peak_spiking
            ax_tfs_tps = fig.add_subplot(3, 5, 1)
            ax_tfs_tps.set_xlabel(tfs_label)
            ax_tfs_tps.set_ylabel(tps_label)
            # t_first_spike - f_peak_spiking
            ax_tfs_fps = fig.add_subplot(3, 5, 2)
            ax_tfs_fps.set_xlabel(tfs_label)
            ax_tfs_fps.set_ylabel(fps_label)
            # t_first_spike - f_avg
            ax_tfs_favg = fig.add_subplot(3, 5, 3)
            ax_tfs_favg.set_xlabel(tfs_label)
            ax_tfs_favg.set_ylabel(favg_label)
            # t_peak_spiking - f_avg
            ax_tps_favg = fig.add_subplot(3, 5, 4)
            ax_tps_favg.set_xlabel(tps_label)
            ax_tps_favg.set_ylabel(favg_label)
            # f_peak_spiking - f_avg
            ax_fps_favg = fig.add_subplot(3, 5, 5)
            ax_fps_favg.set_xlabel(fps_label)
            ax_fps_favg.set_ylabel(favg_label)
            # The axes on second row are for 3D plotting of distributions over stimulus presentations
            # t_first_spike
            ax_tfs_bg = fig.add_subplot(3, 5, 6)
            ax_tfs_bg.set_xlabel('Time to first spike, x=background stim #')
            ax_tfs_bg.set_ylabel('cell #')
            ax_tfs_probe = fig.add_subplot(3, 5, 11)
            ax_tfs_probe.set_xlabel('Time to first spike, x=probe stim #')
            ax_tfs_probe.set_ylabel('cell #')
            # t_peak_spiking
            ax_tps_bg = fig.add_subplot(3, 5, 7)
            ax_tps_bg.set_xlabel('Time to peak spiking, x=background stim #')
            ax_tps_bg.set_ylabel('cell #')
            ax_tps_probe = fig.add_subplot(3, 5, 12)
            ax_tps_probe.set_xlabel('Time to peak spiking, x=probe stim #')
            ax_tps_probe.set_ylabel('cell #')
            # f_peak_spiking
            ax_fps_bg = fig.add_subplot(3, 5, 8)
            ax_fps_bg.set_xlabel('Peak spiking rate, x=background stim #')
            ax_fps_bg.set_ylabel('cell #')
            ax_fps_probe = fig.add_subplot(3, 5, 13)
            ax_fps_probe.set_xlabel('Peak spiking rate, x=probe stim #')
            ax_fps_probe.set_ylabel('cell #')
            # f_avg 
            ax_favg_bg = fig.add_subplot(3, 5, 9)
            ax_favg_bg.set_xlabel('Average spiking rate, x=background stim #')
            ax_favg_bg.set_ylabel('cell #')
            ax_favg_probe = fig.add_subplot(3, 5, 14)
            ax_favg_probe.set_xlabel('Average spiking rate, x=probe stim #')
            ax_favg_probe.set_ylabel('cell #')
            # Now prepare the data and do the plotting
            cells = bgdata.keys()            
            bg_tfs = np.array([bgdata[cell]['t_first_spike'] for cell in cells])
            bg_tps = np.array([bgdata[cell]['t_peak_spiking'] for cell in cells])
            bg_fps = np.array([bgdata[cell]['f_peak_spiking'] for cell in cells])
            bg_favg = np.array([bgdata[cell]['f_avg'] for info in cells])
            probe_tfs = np.array([probedata[cell]['t_first_spike'] for cell in cells])
            probe_tps = np.array([probedata[cell]['t_peak_spiking'] for cell in cells])
            probe_fps = np.array([probedata[cell]['f_peak_spiking'] for cell in cells])
            probe_favg = np.array([probedata[cell]['f_avg'] for cell in cells])
            bg_tfs_mean = np.mean(bg_tfs, 1)
            bg_tps_mean = np.mean(bg_tps, 1)
            bg_fps_mean = np.mean(bg_fps, 1)
            bg_favg_mean = np.mean(bg_favg, 1)
            probe_tfs_mean = np.mean(probe_tfs, 1)
            probe_tps_mean = np.mean(probe_tps, 1)
            probe_fps_mean = np.mean(probe_fps, 1)
            probe_favg_mean = np.mean(probe_favg, 1)
            ax_tfs_tps.scatter(bg_tfs_mean, bg_tps_mean, c='c', marker='x')
            ax_tfs_tps.scatter(probe_tfs_mean, probe_tps_mean, c='m', marker='+')
            ax_tfs_fps.scatter(bg_tfs_mean, bg_fps_mean, c='c', marker='x')
            ax_tfs_fps.scatter(probe_tfs_mean, probe_fps_mean, c='m', marker='+')
            ax_tfs_favg.scatter(bg_tfs_mean, bg_favg_mean, c='c', marker='x')
            ax_tfs_favg.scatter(probe_tfs_mean, probe_favg_mean, c='m', marker='+')
            ax_tps_favg.scatter(bg_tps_mean, bg_favg_mean, c='c', marker='x')
            ax_tps_favg.scatter(probe_tps_mean, probe_favg_mean, c='m', marker='+')
            ax_fps_favg.scatter(bg_fps_mean, bg_favg_mean, c='c', marker='x')
            ax_fps_favg.scatter(probe_fps_mean, probe_favg_mean, c='m', marker='+')
            ax_tfs_bg.pcolor(bg_tfs)
            print 'PROBE TFS'
            print probe_tfs
            if len(probe_tfs) > 0:
                print probe_tfs, len(probe_tfs), probe_tfs.shape
                ax_tfs_probe.pcolor(probe_tfs)
            ax_tps_bg.pcolor(bg_tps)
            ax_tps_probe.pcolor(probe_tps)
            ax_fps_bg.pcolor(bg_fps)
            ax_fps_probe.pcolor(probe_fps)
            ax_favg_bg.pcolor(bg_favg)
            ax_favg_probe.pcolor(probe_favg)
            fig.set_size_inches(20.0, 10.0, forward=True)
            plt.show()
            # raise(Exception)

                

# 
# bgprobe_run.py ends here

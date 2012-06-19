# bgprobe_run.py --- 
# 
# Filename: bgprobe_run.py
# Description: 
# Author: 
# Maintainer: 
# Created: Fri Jun 15 14:40:53 2012 (+0530)
# Version: 
# Last-Updated: Tue Jun 19 12:47:46 2012 (+0530)
#           By: subha
#     Update #: 432
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
    candidate_fh = get_valid_files_handles('/data/subha/rsync_ghevar_cortical_data_clone/')
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
            probed_cells = get_probed_cells(files[0])
            probed_cells = [cell for cell in probed_cells for celltype in celltypes if cell.startswith(celltype) ]
            print '*******************************************'
            print '* Probed cells:'            
            for cell in probed_cells:
                print cell                
            print '*******************************************'
            bgdata, probedata, = collect_statistics(files, celltypes)
            fig = plt.figure()
            # t_first_spike - t_peak_spiking
            ax_tfs_tps = fig.add_subplot(2, 5, 1)
            ax_tfs_tps.set_xlabel(tfs_label)
            ax_tfs_tps.set_ylabel(tps_label)
            # t_first_spike - f_peak_spiking
            ax_tfs_fps = fig.add_subplot(2, 5, 2)
            ax_tfs_fps.set_xlabel(tfs_label)
            ax_tfs_fps.set_ylabel(fps_label)
            # t_first_spike - f_avg
            ax_tfs_favg = fig.add_subplot(2, 5, 3)
            ax_tfs_favg.set_xlabel(tfs_label)
            ax_tfs_favg.set_ylabel(favg_label)
            # t_peak_spiking - f_avg
            ax_tps_favg = fig.add_subplot(2, 5, 4)
            ax_tps_favg.set_xlabel(tps_label)
            ax_tps_favg.set_ylabel(favg_label)
            # f_peak_spiking - f_avg
            ax_fps_favg = fig.add_subplot(2, 5, 5)
            ax_fps_favg.set_xlabel(fps_label)
            ax_fps_favg.set_ylabel(favg_label)
            # t_first_spike
            ax_tfs = fig.add_subplot(2, 5, 6, projection='3d')
            # t_peak_spiking
            ax_tps = fig.add_subplot(2, 5, 7, projection='3d')
            # f_peak_spiking
            ax_fps = fig.add_subplot(2, 5, 8, projection='3d')
            # f_avg 
            ax_favg = fig.add_subplot(2, 5, 9, projection='3d')
            # Now prepare the data and do the plotting
            bg_tfs = np.array([info['t_first_spike'] for info in bgdata.values()])
            bg_tps = np.array([info['t_peak_spiking'] for info in bgdata.values()])
            bg_fps = np.array([info['f_peak_spiking'] for info in bgdata.values()])
            bg_favg = np.array([info['f_avg'] for info in bgdata.values()])
            probe_tfs = np.array([info['t_first_spike'] for info in probedata.values()])
            probe_tps = np.array([info['t_peak_spiking'] for info in probedata.values()])
            probe_fps = np.array([info['f_peak_spiking'] for info in probedata.values()])
            probe_favg = np.array([info['f_avg'] for info in probedata.values()])
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
            ax_tfs_favg.scatter(bg_tfs_mean, bg_favg_mean, c='c', marker='x')
            ax_tfs_favg.scatter(probe_tfs_mean, probe_favg_mean, c='m', marker='+')
            ax_tps_favg.scatter(bg_tps_mean, bg_favg_mean, c='c', marker='x')
            ax_tps_favg.scatter(probe_tps_mean, probe_favg_mean, c='m', marker='+')
            ax_fps_favg.scatter(bg_fps_mean, bg_favg_mean, c='c', marker='x')
            ax_fps_favg.scatter(probe_fps_mean, probe_favg_mean, c='m', marker='+')
            

            # grp = dump.create_group('seed_%s_hash_%d' % (seed, hash_))
            # grp.attrs['files'] = str(','.join([f.filename for f in files]))
            # bgtimes_grp = grp.create_group('first_spike_bg')
            # probetimes_grp = grp.create_group('first_spike_probe')
            # bgcnt_grp = grp.create_group('spikecount_bg')
            # probecnt_grp = grp.create_group('spikecount_probe')
            # bgfreq_grp = grp.create_group('spikefreq_bg')
            # bgfreq_grp.attrs['width'] = width
            # probefreq_grp = grp.create_group('spikefreq_probe')
            # probefreq_grp.attrs['width'] = width        
            # fig = plt.figure()
            # ax1 = fig.add_subplot(211, projection='3d')
            # ax2 = fig.add_subplot(212, projection='3d')
            # for celltype, marker in zip(['SpinyStellate', 'SupPyrRS', 'SupPyrFRB'], ['p', '^', 'o']):
            #     print '###### Celltype', celltype
            #     cells = pick_cells(files, celltype, 100) # Arbitrarily choose hundred cells
            #     if not cells:
            #         print '!!!!!! No entry for celltype', celltype
            #         continue
            #     probed_cell_info = {}
            #     bg_mean_vals = {}
            #     probe_mean_vals = {}
            #     bgtimes, probetimes, = get_stim_aligned_spike_times(files, cells)
            #     bg_time_to_first_spike = {}
            #     probe_time_to_first_spike = {}
            #     bg_spike_freq = {}
            #     probe_spike_freq = {}
            #     bg_spike_count = {}
            #     probe_spike_count = {}
            #     bg_peak_freq_dict = {}
            #     probe_peak_freq_dict = {}
            #     bg_peak_time_dict = {}
            #     probe_peak_time_dict = {}                
            #     for cell in cells:
            #         bg_tfs = get_t_first_spike(bgtimes[cell])
            #         probe_tfs = get_t_first_spike(probetimes[cell])
            #         bg_freq_info = get_max_spike_count(bgtimes[cell], width)
            #         probe_freq_info = get_max_spike_count(probetimes[cell], width)
            #         bg_mean_peak_freq = np.mean(bg_freq_info[:,1])/width
            #         probe_mean_peak_freq = np.mean(probe_freq_info[:,1])/width
            #         bg_mean_peak_time = np.mean(bg_freq_info[:,0])
            #         probe_mean_peak_time = np.mean(probe_freq_info[:,0])
            #         bg_scnt = np.array([len(st) for st in bgtimes[cell]])/isi
            #         probe_scnt = np.array([len(st) for st in probetimes[cell]])/isi
            #         bg_mean_ = [np.mean(bg_tfs), bg_mean_peak_freq, np.mean(bg_scnt)]
            #         probe_mean_ = [np.mean(probe_tfs), probe_mean_peak_freq, np.mean(probe_scnt)]
            #         if cell in probed_cells:
            #             probed_cell_info[cell] = {'bg_tfs': bg_mean_[0],
            #                                       'probe_tfs': probe_mean_[0],
            #                                       'bg_mean_peak_freq': bg_mean_[1],
            #                                       'probe_mean_peak_freq': probe_mean_[1],
            #                                       'bg_mean_peak_time': bg_mean_peak_time,
            #                                       'probe_mean_peak_time': probe_mean_peak_time,
            #                                       'bg_spike_freq': bg_mean_[2],
            #                                       'probe_spike_freq': probe_mean_[2]}
            #         else:
            #             pass
            #             # ax1.plot([bg_mean_[0], probe_mean_[0]], [bg_mean_[1], probe_mean_[1]], [bg_mean_[2], probe_mean_[2]], 'g:')
            #         bg_mean_vals[cell] = bg_mean_
            #         probe_mean_vals[cell] = probe_mean_
            #         bg_peak_freq_dict[cell] = bg_mean_peak_freq
            #         probe_peak_freq_dict[cell] = probe_mean_peak_freq
            #         bg_peak_time_dict[cell] = bg_mean_peak_time
            #         probe_peak_time_dict[cell] = probe_mean_peak_time
            #         bgtimes_grp.create_dataset(cell, data=np.array( bg_tfs))
            #         probetimes_grp.create_dataset(cell, data=np.array( probe_tfs))
            #         bgcnt_grp.create_dataset(cell, data=np.array( bg_scnt))
            #         probecnt_grp.create_dataset(cell, data=np.array( probe_scnt))
            #         bgfreq_grp.create_dataset(cell, data=bg_freq_info)
            #         probefreq_grp.create_dataset(cell, data=probe_freq_info)
            #         bg_time_to_first_spike[cell] = bg_tfs
            #         probe_time_to_first_spike[cell] = probe_tfs
            #         bg_spike_freq[cell] = bg_mean_peak_freq
            #         probe_spike_freq[cell] = probe_mean_peak_freq
            #         bg_spike_freq[cell] = bg_scnt
            #         probe_spike_freq[cell] = probe_scnt
            #     bg_values = np.array(bg_mean_vals.values())
            #     probe_values = np.array(probe_mean_vals.values())
            #     ax1.scatter(bg_values[:,0], bg_values[:,1], bg_values[:,2], c='c', marker=marker)
            #     ax1.scatter(probe_values[:,0], probe_values[:,1], probe_values[:,2], c='m', marker=marker)
            #     ax1.set_xlabel('Time to first spike')
            #     ax1.set_ylabel('Peak spiking rate')
            #     ax1.set_zlabel('Average spike rate')
            #     ax2.scatter(np.array(bg_values[:,0]), np.array(bg_peak_time_dict.values()), np.array(bg_peak_freq_dict.values()), c='c', marker=marker)
            #     ax2.scatter(np.array(probe_values[:,0]), np.array(probe_peak_time_dict.values()), np.array(probe_peak_freq_dict.values()), c='m', marker=marker)
            #     ax2.set_xlabel('Time to first spike')
            #     ax2.set_ylabel('Peak spiking time')
            #     ax2.set_zlabel('Peak spiking rate')
            #     for value in probed_cell_info.values():
            #         ax1.scatter(np.array([value['bg_tfs']]),
            #                  np.array([value['bg_mean_peak_freq']]),
            #                  np.array([value['bg_spike_freq']]),
            #                     c='b', marker=marker, edgecolors='y')
            #         ax1.scatter(np.array([value['probe_tfs']]),
            #                  np.array([value['probe_mean_peak_freq']]),
            #                  np.array([value['probe_spike_freq']]),
            #                     c='r', marker=marker, edgecolors='y')
            #         ax2.scatter(np.array([value['bg_tfs']]),
            #                  np.array([value['bg_mean_peak_time']]),
            #                  np.array([value['bg_mean_peak_freq']]),
            #                     c='b', marker=marker, edgecolors='y')
            #         ax2.scatter(np.array([value['probe_tfs']]),
            #                  np.array([value['probe_mean_peak_time']]),
            #                  np.array([value['probe_mean_peak_freq']]),
            #                     c='r', marker=marker, edgecolors='y')
                # for value in probed_cell_info.values():
                #     ax1.plot(np.array([value['bg_tfs'], value['probe_tfs']]),
                #              np.array([value['bg_mean_peak_freq'], value['probe_mean_peak_freq']]),
                #              np.array([value['bg_spike_freq'], value['probe_spike_freq']]),
                #                 'r-')
                #     ax2.plot(np.array([value['bg_tfs'], value['probe_tfs']]),
                #              np.array([value['bg_mean_peak_time'], value['probe_mean_peak_time']]),
                #              np.array([value['bg_mean_peak_freq'], value['probe_mean_peak_freq']]),
                #                 'r-')
            fig.set_size_inches(15, 6)
            plt.show()

                

# 
# bgprobe_run.py ends here

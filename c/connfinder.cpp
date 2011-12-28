// connfinder.cpp --- 
// 
// Filename: connfinder.cpp
// Description: 
// Author: 
// Maintainer: 
// Created: Mon Dec 26 15:06:27 2011 (+0530)
// Version: 
// Last-Updated: Wed Dec 28 16:04:25 2011 (+0530)
//           By: Subhasis Ray
//     Update #: 344
// URL: 
// Keywords: 
// Compatibility: 
// 
// 

// Commentary: 
// 
// This code is for finding connectivity using various correlation
// methods from spike trains.
// 
// 

// Change log:
// 
// Starting with cross correlation between spike trains.
// 
// 

// Code:

#include <iostream>
#include <fstream>
#include <map>
#include <vector>
#include <set>
#include <algorithm>
#include <string>

#include <cassert>
#include <cstdlib>
#include <cmath>
#include <cstring>

#include "hdf5.h"
#include "hdf5_hl.h"

using namespace std;

herr_t spike_data_op(hid_t loc_id, const char * name, const H5L_info_t * info, void * operator_data)
{
    vector< pair< string, vector<double> > > * data_list = (vector < pair < string, vector < double > > >*)operator_data;
    herr_t status;
    H5O_info_t infobuf;
    cout << "spike_data_op: reading " << name << endl;
    status = H5Oget_info_by_name(loc_id, name, &infobuf, H5P_DEFAULT);
    if (status < 0) {
        cerr << "Error getting info for " << name << endl;
        return status;
    }
    if (infobuf.type == H5O_TYPE_DATASET){
        vector<double> data;
        hid_t dset_id = H5Dopen(loc_id, name);
        hid_t filespace_id = H5Dget_space(dset_id);
        int rank = H5Sget_simple_extent_ndims(filespace_id);
        cout << name << ", rank: " << rank << endl;
        hsize_t dims[2];
        status = H5Sget_simple_extent_dims(filespace_id, dims, NULL);
        cout << "Dataset size is: " << dims[0] << endl;
        // This is unsafe, I should check that double is same size as HDF5 double.
        data.resize(dims[0]);
        hid_t props = H5Dget_create_plist(dset_id);
        if (H5D_CHUNKED == H5Pget_layout(props)){
            hsize_t chunk_dims[2];
            int rank_chunk = H5Pget_chunk(props, 2, chunk_dims);
            cout << "chunk rank " << rank_chunk << ", dimensions " << chunk_dims[0] << "x" << chunk_dims[1] << endl;
        }
        hid_t memspace_id = H5Screate_simple(1, dims, NULL);
        status = H5Dread(dset_id, H5T_NATIVE_DOUBLE, memspace_id, filespace_id, H5P_DEFAULT, &data[0]);
        // status = H5LTread_dataset_double(loc_id, name, &data[0]);
        H5Dclose(dset_id);
        data_list->push_back(pair < string, vector< double > > (string(name), data));
    }
    return 0;
}

herr_t get_spike_data(const hid_t file, vector< pair< string, vector <double> > >& data)
{
    hid_t spike_group = H5Gopen(file, "spikes");
    H5G_info_t group_info;
    herr_t status = H5Gget_info(spike_group, &group_info);
    if (status < 0){
        cerr << "Error opening group spikes. H5Gget_info returned " << status << endl;
        H5Gclose(spike_group);
        return status;
    }
    hsize_t num_datasets = group_info.nlinks;
    if (num_datasets > 0){
        cout << "Number of datasets: " << num_datasets << endl;
        status = H5Literate(spike_group, H5_INDEX_NAME, H5_ITER_NATIVE, NULL, spike_data_op, &data);
    } else {
        H5Gclose(spike_group);
        cerr << "No data set inside spikes group." << endl;
        return -1;
    }
    H5Gclose(spike_group);
    return status;
}

/**
   Calculate spiking rates from spike times taking data between .

   spike_data - input vector of spike time data. Each element of
   spike_data is a pair consisiting of a cell name and a vector
   containing the spike times for that cell.

   spiking_rate - output vector of pairs of (cell-name, data-vector).

   t_total - total real time (in seconds) for the data.

   dt - time interval between successive data points (sampling interval for original data).

   binsize - size of frequency bins in seconds

   start - all data points recorded before this time are not included in frequency computation. Default 0.

   end - all data points recorded after this time are excluded from computation. If < 0, whole time series is considered.

   

   
 */
void compute_spiking_rate(vector < pair < string, vector < double > > > & spike_data,
                          vector < pair < string, vector < double > > > & spiking_rate,
                          double t_total,
                          double binsize=1.0,
                          size_t start=0.0,
                          double end=-1.0)
{
    if (end < 0){
        end = t_total;
    }
    // number of bins in the output dataset
    size_t num_bins = (int)((end - start) / binsize + 1);
    spiking_rate.clear();
    for (size_t ii = 0; ii < spike_data.size(); ++ii){
        // Initialize number of spikes in each bin to 0
        vector <double> frequency_data(num_bins, 0.0);
        // Go through all the spike times
        for (size_t jj = start; jj < spike_data[ii].second.size() && spike_data[ii].second[jj] < end; ++jj){
            // If spike time is before start time, ignore
            if (spike_data[ii].second[jj] < start){
                continue;
            }
            // Index of the bin on which this spike is centred
            int index = (int)(spike_data[ii].second[jj] / binsize + 0.5);
            // Increase spike count in each bin around the central bin to which this spike contributes
            if (index - 1 > 0){
                    frequency_data[index-1] += 1;
            }
            frequency_data[index] += 1;
        }
        spiking_rate.push_back(pair < string, vector < double > > (spike_data[ii].first, frequency_data));
    }
}

int main(int argc, char **argv)
{
    if (argc < 3){
        cout << "Usage:" << argv[0] << " <input_file> <outputfile> " << endl;
        return 1;
    }
    string input_file_name(argv[1]);
    string output_file_name(argv[2]);
    hid_t data_file_id = H5Fopen(input_file_name.c_str(), H5F_ACC_RDONLY, H5Pcreate(H5P_FILE_ACCESS));
    
    vector< pair < string, vector <double> > > spike_data;
    herr_t status = get_spike_data(data_file_id, spike_data);
    H5Fclose(data_file_id);
    ofstream outfile(output_file_name.c_str());
    for (unsigned int ii = 0; ii < spike_data.size(); ++ ii){
        pair< string, vector < double > > data = spike_data[ii];
        outfile << data.first << ", " << data.second.size() << endl;
    }
    vector < pair < string, vector < double > > > spike_rate;
    // This is test, t_total may vary from simulation to simulation
    compute_spiking_rate(spike_data, spike_rate, 5.0, 0.25e-3);
    for (unsigned int ii = 0; ii < spike_rate.size(); ++ii){
        outfile << spike_data[ii].first << " ";
        for (unsigned int jj = 0; jj < spike_rate[ii].second.size(); ++jj){
            outfile << spike_rate[ii].second[jj] << " ";
        }
        cout << endl;
    }
    return status;
}



// 
// connfinder.cpp ends here

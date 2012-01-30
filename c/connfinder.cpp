// connfinder.cpp --- 
// 
// Filename: connfinder.cpp
// Description: 
// Author: 
// Maintainer: 
// Created: Mon Dec 26 15:06:27 2011 (+0530)
// Version: 
// Last-Updated: Mon Jan 30 20:43:02 2012 (+0530)
//           By: subha
//     Update #: 673
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
#include <unistd.h>

#include "hdf5.h"
#include "hdf5_hl.h"

using namespace std;

void compute_spiking_rate(vector < double > & spike_data,
                          vector < double > & spike_rate,
                          double t_total,
                          double binsize=1.0,
                          double start=0.0,
                          double end=-1.0);
herr_t collect_spike_name(const hid_t loc_id, const char * name, const H5L_info_t * info, void * operator_data)
{
    vector < string > * spike_names = static_cast< vector < string > * >(operator_data);
    assert(spike_names != NULL);
    herr_t status;
    H5O_info_t infobuf;
    status = H5Oget_info_by_name(loc_id, name, &infobuf, H5P_DEFAULT);
    if (status < 0){
        cerr << "collect_spike_name: Error getting info on " << name << endl;
        return status;
    }
    if ( H5O_TYPE_DATASET == infobuf.type ) {
        spike_names->push_back(string(name));
        cout << "Found " << name << endl;
    }
    return 0;        
}

herr_t get_spike_dataset_names(const hid_t file_id, vector<string>& names){
    names.clear();
    hid_t spike_group = H5Gopen(file_id, "spikes", H5P_DEFAULT);
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
        status = H5Literate(spike_group, H5_INDEX_NAME, H5_ITER_NATIVE, NULL, collect_spike_name, &names);
    } else {
        H5Gclose(spike_group);
        cerr << "No data set inside spikes group." << endl;
        return -1;
    }
    H5Gclose(spike_group);
    return status;
}

typedef struct key_value_pair{
    char key[16];
    char value[16];
}key_value_pair;
herr_t dump_spike_rates(const hid_t file_id, hid_t output_file_id, double & t_total, double binsize=1.0, double start=0, double end=-1)
{
    vector < string > cells;
    herr_t status = get_spike_dataset_names(file_id, cells);
    if (status < 0) {
        return status;
    }
    t_total = -1.0;

    hid_t runcfg_node = H5Gopen(file_id, "runconfig", H5P_DEFAULT);    
    size_t dst_size = sizeof(key_value_pair);
    key_value_pair buf[5]; // that is the number of entries under scheduling, pain of C that I have to specify it beforehand    size_t dst_size = sizeof(key_value_pair);
    size_t dst_field_sizes[2] = {sizeof(buf[0].key),
                                 sizeof(buf[0].value)};

    size_t dst_offset[2] = { HOFFSET(key_value_pair, key),
                             HOFFSET(key_value_pair, value)};
    status = H5TBread_table(runcfg_node, "scheduling", dst_size, dst_offset, dst_field_sizes, buf);
    if (status < 0) {
        H5Gclose(runcfg_node);
        H5Fclose(output_file_id);
        return status;
    }
    H5Gclose(runcfg_node);    
    for (int ii = 0; ii < 5; ++ii){
        if (string(buf[ii].key) == "simtime"){
            t_total = atof(buf[ii].value);
            break;
        }
    }
    if (t_total < 0){
        cerr << "dump_spike_rates: could not obtain simulation time." << endl;
        H5Fclose(output_file_id);
        return -1;
    }
    hid_t spike_rate_group = H5Gcreate(output_file_id, "spikerate", H5P_DEFAULT, H5P_DEFAULT, H5P_DEFAULT);
    
    hid_t spike_group = H5Gopen(file_id, "spikes", H5P_DEFAULT);
    
    for (unsigned int ii = 0; ii < cells.size(); ++ii){
        vector < double > spike_data;
        hsize_t dims[2];
        hid_t spike_info;
        size_t type_size;
        H5T_class_t type_class;
        status = H5LTget_dataset_info(spike_group, cells[ii].c_str(), dims, &type_class, &type_size);
        if (status < 0){
            H5Gclose(spike_group);
            H5Fclose(output_file_id);
            return status;
        }
        cout << "Found dataset info for " << cells[ii] << ": size: " << type_size << endl;
                                                       
        spike_data.resize(dims[0]);
        status = H5LTread_dataset_double(spike_group, cells[ii].c_str(), &spike_data[0]);
        if (status < 0){
            H5Gclose(spike_group);
            H5Fclose(output_file_id);
            return status;
        }
        cout << "Read dataset for " << cells[ii] << endl;
        vector < double > spike_rate;
        compute_spiking_rate(spike_data, spike_rate, t_total, binsize, start, end);
        dims[0] = spike_rate.size();
        dims[1] = 2;
        double * dataset = new double[2 * spike_rate.size()];
        double t = start + binsize/2.0;
        for (unsigned jj = 0; jj < spike_rate.size(); jj ++){
            dataset[2*jj] = t;
            dataset[2*jj+1] = spike_rate[jj];
            t += binsize/2.0;
        }
        status = H5LTmake_dataset_double(spike_rate_group, cells[ii].c_str(), 2, dims, dataset);
        if (status < 0){
            cerr << "Could not create dataset " << cells[ii] << endl;
            H5Gclose(spike_group);
            H5Fclose(output_file_id);
            return status;
        }
    }
    H5Gclose(spike_group);
    H5Fclose(output_file_id);
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
void compute_spiking_rate(vector < double > & spike_data,
                          vector < double > & spike_rate,
                          double t_total,
                          double binsize,
                          double start,
                          double end)
{
    if (end < 0){
        end = t_total;
    }
    // number of bins in the output dataset
    size_t num_bins = (int)(2 * (end - start) / binsize - 1);
    // Initialize number of spikes in each bin to 0
    spike_rate.assign(num_bins, 0.0);
    // Go through all the spike times
    double t = start;
    for (unsigned int ii = 0; ii < num_bins; ++ii){
        for (unsigned int jj = 0; jj < spike_data.size(); ++jj){
            if (spike_data[jj] < start){
                continue;
            }
            if (spike_data[jj] < t){
                if ( spike_data[jj] > t - binsize/2.0 ) {
                    spike_rate[ii] += 1.0;
                }
            } else if (spike_data[jj] <= t + binsize/2.0) {
                spike_rate[ii] += 1.0;
            }
        }
        t += binsize/2.0;
    }
}

int main(int argc, char **argv)
{
    if (argc < 3){
        cout << "Usage:" << argv[0] << " [-t <binsize-in-seconds>] -i <input_file> -o <outputfile> " << endl;
        return 1;
    }
    int char_code = 0;
    float binsize = 1.0;
    float start = 0.0;
    float end = -1.0;
    
    string input_file_name, output_file_name;
    while ((char_code = getopt(argc, argv, "b:s:e:i:o:")) != -1){
        cout << "charcode: " << (char)char_code << ", arg: " << string(optarg) << endl;
        if (char_code == 'b'){
            binsize = atof(optarg);
        } else if (char_code == 's'){
            start = atof(optarg);
        } else if (char_code == 'e') {
            end = atof(optarg);
        } else if (char_code == 'i'){
            input_file_name = string(optarg);
        } else if (char_code == 'o'){
            output_file_name = string(optarg);
        }
    }
    hid_t output_file_id = H5Fcreate(output_file_name.c_str(), H5F_ACC_EXCL, H5P_DEFAULT, H5P_DEFAULT);
    if (output_file_id < 0 ){
        cerr << "Failed to open file " << output_file_name << " for writing. Check if file already exists." << endl;
        return 1;
    }
    hid_t data_file_id = H5Fopen(input_file_name.c_str(), H5F_ACC_RDONLY, H5Pcreate(H5P_FILE_ACCESS));
    if (data_file_id < 0){
        cerr << "Failed to open file " << input_file_name << " for writing. Check if file already exists." << endl;
        return 2;
    }
    // Ignore the first second - because it is used for stabilizing
    double t_total = 0.0;
    dump_spike_rates(data_file_id, output_file_id, t_total, binsize, start, end);
    H5Fclose(data_file_id);
    return 0;
}



// 
// connfinder.cpp ends here

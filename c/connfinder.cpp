// connfinder.cpp --- 
// 
// Filename: connfinder.cpp
// Description: 
// Author: 
// Maintainer: 
// Created: Mon Dec 26 15:06:27 2011 (+0530)
// Version: 
// Last-Updated: Tue Dec 27 17:28:00 2011 (+0530)
//           By: subha
//     Update #: 212
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


// herr_t collect_spikedata(hid_t loc_id, const char * name, const H5L_info_t * info, void * operator_data)
// {
//     herr_t status;
//     H5O_info_t infobuf;
//     status = H5O_get_info_by_name(loc_id, name, &infobuf, H5P_DEFAULT);
//     if (infobuf.type == H5O_TYPE_DATASET){
//         spike_names[COUNT] = (char*)calloc(sizeof(char), strlen(name));
//         strncpy(spike_names[COUNT], name, VSNAMELENMAX);
//         int length = 0;
//         status = H5LTget_dataset_ndims(loc_id, name, &length);
//         if (status < 0){
//             cerr << "Error getting dataset dims for " << name << ". H5LTget_dataset_ndims returned : " << status << endl;
//             free(spike_names[COUNT]);
//             return status;
//         }
//         operator_data = (double*)calloc(sizeof(double), (size_t)length);
//         status = H5LTread_dataset_double(loc_id, name, spike_data[COUNT]);
//         if (status < 0){
//             cerr << "Error reading dataset for " << name << ". H5LTread_dataset_ndims returned : " << status << endl;
//             free(spike_names[COUNT]);
//             free(spike_data[COUNT]);
//             return status;
//         }        
//     }
//     return 0;
// }


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
        hid_t memspace_id;
        int rank = H5Sget_simple_extent_ndims(filespace_id);
        cout << name << ", rank: " << rank << endl;
        hsize_t dims[2];
        status = H5Sget_simple_extent_dims(filespace_id, dims, NULL);
        cout << "Dataset size is: " << size << endl;
        // This is unsafe, I should check that double is same size as HDF5 double.
        data.resize(size);
        hsize_t dims[] = {size};
        hid_t memtype_id = H5Tarray_create(H5T_NATIVE_DOUBLE, 1, dims, 0);
        // status = H5Dread(dset_id, memtype_id, H5S_ALL, H5S_ALL, H5P_DEFAULT, &data[0]);
        status = H5LTread_dataset_double(loc_id, name, &data[0]);
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
    for (unsigned int ii = 0; ii < spike_data.size(); ++ ii){
        pair< string, vector < double > > data = spike_data[ii];
        cout << data.first << ", " << data.second.size() << endl;
    }
    return status;
}



// 
// connfinder.cpp ends here

// synstat.cpp --- 
// 
// Filename: synstat.cpp
// Description: 
// Author: 
// Maintainer: 
// Created: Mon Dec  5 11:04:40 2011 (+0530)
// Version: 
// Last-Updated: Tue Dec  6 16:44:36 2011 (+0530)
//           By: subha
//     Update #: 472
// URL: 
// Keywords: 
// Compatibility: 
// 
// 

// Commentary: 
// 
// This is for extracting some stats about the synapses from network model.
// 
// 

// Change log:
// 
// 
// 
// 
// This program is free software; you can redistribute it and/or
// modify it under the terms of the GNU General Public License as
// published by the Free Software Foundation; either version 3, or
// (at your option) any later version.
// 
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
// General Public License for more details.
// 
// You should have received a copy of the GNU General Public License
// along with this program; see the file COPYING.  If not, write to
// the Free Software Foundation, Inc., 51 Franklin Street, Fifth
// Floor, Boston, MA 02110-1301, USA.
// 
// 

// Code:

#include <iostream>
#include <fstream>
#include <map>
#include <set>
#include <algorithm>
// #include <pair>
#include <string>

#include <cassert>
#include <cstdlib>
#include <cmath>

// #include "hdf.h"
// #include "hdf5_hl.h"
#include "H5Cpp.h"

using namespace std;
using namespace H5;


typedef struct syn_t{
    char src[32];
    char dest[32];
    char type[4];
    float Gbar;
    float tau1;
    float tau2;
    float Ek;
} syn_t;
struct comparator{
    bool  operator()(const string& left, const string& right) const
    {
        string lcelltype = left.substr(0, left.find('_'));
        int lcellnum = atol(left.substr(left.find('_')+1).c_str());
        string rcelltype = right.substr(0, right.find('_'));
        int rcellnum = atol(right.substr(right.find('_')+1).c_str());
        if (lcelltype == rcelltype){
            return lcellnum < rcellnum;
        }
        return lcelltype < rcelltype;
    }
};
const H5std_string DATA_SET_PATH("/network/synapse");

/**
   Read synapse list from hdf5 dataset and for each cell store the
   total Gbar for each synapse type (ampa, nmda, gaba).
 */
void cell_syn_stat(const DataSet& syndataset,
                   set<string, comparator>& cellset,
                   map<string, double>& cell_ampa_map,
                   map<string, double>& cell_nmda_map,
                   map<string, double>& cell_gaba_map){
    DataSpace dataspace;
    try{
        dataspace = syndataset.getSpace();
    } catch (DataSetIException error){
        error.printError();
        return;
    }
    hsize_t len = dataspace.getSimpleExtentNpoints();
    syn_t * gbar_dataset = (syn_t*)calloc(len, sizeof(syn_t));
    assert(gbar_dataset != NULL);
    syndataset.read(gbar_dataset, syndataset.getDataType());
    // This block reads in all the synapses and sums up the gbar on
    // all compartments for each cell
    for (hsize_t ii = 0; ii < len; ++ii){
        map<string, double> * sum_map;
        // Update total Gbar for each cell
        if (string(gbar_dataset[ii].type, 4) == "ampa"){
            sum_map = &cell_ampa_map;
        } else if (string(gbar_dataset[ii].type, 4) == "nmda"){
            sum_map = &cell_nmda_map;
        } else if (string(gbar_dataset[ii].type, 4) == "gaba"){
            sum_map = &cell_gaba_map;
        } else {
            cerr << "Error: unrecognized synapse type '" << gbar_dataset[ii].type << " on " << gbar_dataset[ii].dest << endl;
            continue;
        }
        string comp_path(gbar_dataset[ii].dest);
        string cellname = comp_path.substr(0, comp_path.rfind('/'));
        cellset.insert(cellname);
        map<string, double>::iterator it = sum_map->find(cellname);
        if (it == sum_map->end()){
            sum_map->insert(pair<string, double>(cellname, gbar_dataset[ii].Gbar));
        } else {
            it->second += gbar_dataset[ii].Gbar;
        }
    }
    free(gbar_dataset);    
}

/**
   Given a cell-to-total gbar map, fill up maps for
   celltype->cellcount, celltype->mean(gbar), celltype->var(gbar).
 */
void celltype_syn_stat(const map<string, double>& cell_syn_map,
                       map<string, int>& cellcount_map,
                       map<string, double>& celltype_mean_map,
                       map<string, double>& celltype_var_map){
    for (map<string, double>::const_iterator ii = cell_syn_map.begin(); ii != cell_syn_map.end(); ++ii){
        string celltype = ii->first.substr(0, ii->first.find('_'));
        map<string, int>::iterator it = cellcount_map.find(celltype);
        if (it == cellcount_map.end()){
            cellcount_map.insert(pair<string, int>(celltype, 1));
        } else {
            it->second += 1;
        }
        map<string, double>::iterator syn_it = celltype_mean_map.find(celltype);
        if (syn_it == celltype_mean_map.end()){
            celltype_mean_map.insert(pair<string, double>(celltype, ii->second));
        } else {
            syn_it->second += ii->second;
        }
    }
    for (map<string, double>::iterator ii = celltype_mean_map.begin(); ii != celltype_mean_map.end(); ++ii) {
        ii->second = ii->second / cellcount_map[ii->first];
    }
    for ( map<string, double>::const_iterator ii = cell_syn_map.begin(); ii != cell_syn_map.end(); ++ii) {
        string celltype = ii->first.substr(0, ii->first.find('_'));
        map<string, double>::iterator mean_it = celltype_mean_map.find(celltype);
        map<string, double>::iterator var_it = celltype_var_map.find(celltype);        
        if (var_it == celltype_var_map.end()) {
            celltype_var_map.insert(pair<string, double>(celltype, (ii->second - mean_it->second) * (ii->second - mean_it->second)));
        } else {
            var_it->second += (ii->second - mean_it->second) * (ii->second - mean_it->second);
        }
    }
    for (map<string, double>::iterator ii = celltype_var_map.begin(); ii != celltype_var_map.end(); ++ii) {
        ii->second = sqrt(ii->second / cellcount_map[ii->first]);
    }
}


void synstat(const DataSet& syndataset, ofstream& outfile)
{
    
    map<string, double> cell_ampa_map, cell_nmda_map, cell_gaba_map;
    set<string, comparator> cellset;
    cell_syn_stat(syndataset, cellset, cell_ampa_map, cell_nmda_map, cell_gaba_map);
    for (set<string>::const_iterator it = cellset.begin(); it != cellset.end(); ++it){
        outfile << *it
                << ", " << cell_ampa_map[*it] << ", " << cell_nmda_map[*it] << ", " << cell_gaba_map[*it] << endl;
    }
    map<string, int> cellcount_ampa, cellcount_nmda, cellcount_gaba;
    map<string, double> celltype_ampa_mean, celltype_ampa_var,
            celltype_nmda_mean, celltype_nmda_var,
            celltype_gaba_mean, celltype_gaba_var;
    celltype_syn_stat(cell_ampa_map, cellcount_ampa, celltype_ampa_mean, celltype_ampa_var);
    celltype_syn_stat(cell_nmda_map, cellcount_nmda, celltype_nmda_mean, celltype_nmda_var);
    celltype_syn_stat(cell_gaba_map, cellcount_gaba, celltype_gaba_mean, celltype_gaba_var);    
    outfile << "###############################" << endl;
    string celltypes[] = {
        "SupPyrRS",
        "SupPyrFRB", 
        "SupBasket", 
        "SupAxoaxonic", 
        "SupLTS", 
        "SpinyStellate",
        "TuftedIB", 
        "TuftedRS", 
        "DeepBasket", 
        "DeepAxoaxonic", 
        "DeepLTS", 
        "NontuftedRS", 
        "TCR", 
        "nRT",
        "" // sentinel
    };
    for (string * ptr = &celltypes[0]; !ptr->empty(); ++ptr){
        outfile << *ptr << endl << "------------------" << endl
                << "ampa\t" << celltype_ampa_mean[*ptr] << "\t" << celltype_ampa_var[*ptr] << endl
                << "nmda\t" << celltype_nmda_mean[*ptr] << "\t" << celltype_nmda_var[*ptr] << endl
                << "gaba\t" << celltype_gaba_mean[*ptr] << "\t" << celltype_gaba_var[*ptr] << endl;
    }        
}

int main(int argc, char ** argv)
{
    if (argc < 3){
        cout << "Usage:" << argv[0] << " <filename> <outputfilename> - display some statistics of specified synapse."  << endl;
        return 0;
    }

    const H5std_string FILE_NAME(argv[1]);
    ofstream outfile;
    outfile.open(argv[2]);
    try{
        H5File * file = new H5File(FILE_NAME, H5F_ACC_RDONLY);
        Group * netgroup = new Group(file->openGroup("network"));
        const DataSet * syndataset = new DataSet(netgroup->openDataSet("synapse"));
        synstat(*syndataset, outfile);
        file->close();
        outfile.close();
    }
    catch( FileIException error )
    {
       error.printError();
       return -1;
    }
 
    // catch failure caused by the DataSet operations
    catch( DataSetIException error )
    {
       error.printError();
       return -1;
    }
 
    // catch failure caused by the DataSpace operations
    catch( DataSpaceIException error )
    {
       error.printError();
       return -1;
    }
 
    // catch failure caused by the DataSpace operations
    catch( DataTypeIException error )
    {
       error.printError();
       return -1;
    }    
    return 0;
}
// 
// synstat.cpp ends here

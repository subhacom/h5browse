// synstat.cpp --- 
// 
// Filename: synstat.cpp
// Description: 
// Author: 
// Maintainer: 
// Created: Mon Dec  5 11:04:40 2011 (+0530)
// Version: 
// Last-Updated: Mon Dec  5 19:37:35 2011 (+0530)
//           By: subha
//     Update #: 210
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
#include <map>
// #include <pair>
#include <string>

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
    char syntype[4];
    float Gbar;
    float tau1;
    float tau2;
    float Ek;
} syn_t;

const H5std_string DATA_SET_PATH("/network/synapse");

void synstat(const DataSet * syndataset)
{
    const H5std_string SOURCE("source");
    const H5std_string DEST("dest");
    const H5std_string TYPE("type");
    const H5std_string GBAR("Gbar");
    const H5std_string TAU1("tau1");
    const H5std_string TAU2("tau2");
    const H5std_string EK("Ek");

    // typedef struct gbar_t{
    //     char src[32];
    //     char dest[32];
    //     char type[4];
    //     float Gbar;        
    // } gbar_t;

    CompType syntype(sizeof(syn_t));
    syntype.insertMember(SOURCE, HOFFSET(syn_t, src), StrType(PredType::NATIVE_CHAR, 32));
    syntype.insertMember(DEST, HOFFSET(syn_t, dest), StrType(PredType::NATIVE_CHAR, 32));
    syntype.insertMember(TYPE, HOFFSET(syn_t, syntype), StrType(PredType::NATIVE_CHAR, 4));
    syntype.insertMember(GBAR, HOFFSET(syn_t, Gbar), PredType::NATIVE_FLOAT);
    syntype.insertMember(TAU1, HOFFSET(syn_t, tau1), PredType::NATIVE_FLOAT);
    syntype.insertMember(TAU2, HOFFSET(syn_t, tau2), PredType::NATIVE_FLOAT);
    syntype.insertMember(EK, HOFFSET(syn_t, Ek), PredType::NATIVE_FLOAT);
    cout << "A" << endl;
    
    DataSpace dataspace;
    try{
        dataspace = syndataset->getSpace();
    } catch (DataSetIException error){
        error.printError();
        return;
    }
    cout << "A.0" << endl;
    hsize_t len = dataspace.getSimpleExtentNpoints();
    cout << "A.1" << endl;
    syn_t * gbar_dataset = (syn_t*)calloc(len, sizeof(syn_t));
    cout << "B" << endl;
    syndataset->read(gbar_dataset, syndataset->getDataType());
    cout << "C" << endl;
    map<string, double> sum_map, celltype_sum_map, celltype_var_map;
    map<string, int> cellcount;
    for (hsize_t ii = 0; ii < len; ++ii){
        map<string, double>::iterator it;
        string comp_name = gbar_dataset[ii].dest;
        string cellname = comp_name.substr(0, comp_name.rfind('/'));
        // cout << "cellname: " << cellname << endl;
        string cellclassname = cellname.substr(0, cellname.rfind('_'));
        // cout << "cellclass: " << cellclassname << endl;
        // Update total Gbar for each cell
        it = sum_map.find(cellname);
        if (it == sum_map.end()){
            sum_map.insert(pair<string, double>(cellname, gbar_dataset[ii].Gbar));            
        } else {
            sum_map[cellname] += gbar_dataset[ii].Gbar;
        }
        // Update the total Gbar for each cell type
        it = celltype_sum_map.find(cellclassname);
        if (it == sum_map.end()){
            celltype_sum_map.insert(pair<string, double>(cellclassname, gbar_dataset[ii].Gbar));
        } else {
            celltype_sum_map[cellclassname] += gbar_dataset[ii].Gbar;
        }
        // Track the count of cells of each type
        map<string, int>::iterator it_count = cellcount.find(cellclassname);
        // TODO - this counts number of synapses into each cell type. Need to get actual cellcount.
        if (it_count == cellcount.end()){
            cellcount.insert(pair<string, double>(cellclassname, 1));
        } else {
            cellcount[cellclassname] += 1;
        }
    }
    cout << "D" << endl;
    // calculate the average Gbar for each cell class
    for (map<string, double>::iterator ii = celltype_sum_map.begin(); ii != celltype_sum_map.end(); ++ii){
        ii->second = ii->second/cellcount[ii->first];
        celltype_var_map.insert(pair<string, double>(ii->first, 0.0));
    }
    for (map<string, double>::iterator ii = sum_map.begin(); ii != sum_map.end(); ++ii){
        string cellclass = ii->first.substr(0, ii->first.rfind('_'));        
        celltype_var_map[cellclass] += (ii->second - celltype_sum_map[cellclass]) * (ii->second - celltype_sum_map[cellclass]);
    }            
    for (map<string, double>::iterator ii = celltype_var_map.begin(); ii != celltype_var_map.end(); ++ii){
        ii->second = ii->second/cellcount[ii->first];
    }
    for (map<string, int>::iterator ii = cellcount.begin(); ii != cellcount.end(); ++ii){
        cout << ii->first << ", " << ii->second << ", " << celltype_sum_map[ii->first] << ", " << celltype_var_map[ii->first] << endl;
    }
    cout << "#############################" << endl;
    for (map<string, double>::iterator ii = sum_map.begin(); ii != sum_map.end(); ++ii){
        cout << ii->first << ", " << ii->second << endl;
    }
}

int main(int argc, char ** argv)
{
    if (argc < 2){
        cout << "Usage:" << argv[0] << " <filename> - display some statistics of specified synapse."  << endl;
        return 0;
    }

    const H5std_string FILE_NAME(argv[1]);

    try{
        H5File * file = new H5File(FILE_NAME, H5F_ACC_RDONLY);
        Group * netgroup = new Group(file->openGroup("network"));
        const DataSet * syndataset = new DataSet(netgroup->openDataSet("synapse"));
        synstat(syndataset);
        file->close();
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

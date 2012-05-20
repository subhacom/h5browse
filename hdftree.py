# hdftree.py --- 
# 
# Filename: hdftree.py
# Description: 
# Author: Subhasis Ray
# Maintainer: 
# Copyright (C) 2010 Subhasis Ray, all rights reserved.
# Created: Fri Mar  4 17:54:30 2011 (+0530)
# Version: 
# Last-Updated: Sat May 19 12:23:08 2012 (+0530)
#           By: Subhasis Ray
#     Update #: 499
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

# Code:

import sys
import os
import re
import h5py
import numpy
from PyQt4 import Qt, QtCore, QtGui

class H5TreeWidgetItem(QtGui.QTreeWidgetItem):
    def __init__(self, parent, h5node):
        QtGui.QTreeWidgetItem.__init__(self, parent)
        self.h5node = h5node
        if isinstance(h5node, h5py.File):
            self.setText(0, QtCore.QString(h5node.filename))
        else:
            self.setText(0, QtCore.QString(h5node.name.rpartition('/')[-1]))

    def path(self):        
        path = str(self.data(0, Qt.Qt.DisplayRole).toString())
        parent = self.parent()
        root = self.treeWidget().invisibleRootItem()
        while parent is not None:
            path = str(parent.data(0, Qt.Qt.DisplayRole).toString()) + "/" + path
            parent = parent.parent()
        return str(path)

    def getAttributes(self):
        return self.h5node.attrs

        
    def getHDF5Data(self):
        if isinstance(self.h5node, h5py.Dataset):
            return self.h5node
        else:
            return None
            

class H5TreeWidget(QtGui.QTreeWidget):
    def __init__(self, *args):
        QtGui.QTreeWidget.__init__(self, *args)
        self.fhandles = {}
        self.header().hide()
        
    def addH5Handle(self, filename):
        if not filename.startswith('/'):
            filename = os.path.abspath(filename)
        if not filename in self.fhandles.keys():
            file_handle = h5py.File(filename, 'r')
            self.fhandles[filename] = file_handle
            item = H5TreeWidgetItem(self, file_handle)
            self.addTopLevelItem(item)
            item.setText(0, QtCore.QString(filename))
            self.addTree(item, file_handle)
            
    def addTree(self, currentItem, node):
        if isinstance(node, h5py.Group) or isinstance(node, h5py.File):
            for child in node:
                item = H5TreeWidgetItem(currentItem, node[child])
                self.addTree(item, node[child])

    def getData(self, path):
        path = str(path)
        filename = None
        h5f = None
        for key, value in self.fhandles.items():
            if path.startswith(key):
                filename = key
                path = path[len(filename):] # 1 for '/'
                h5f = value
                break
        if filename is None:
            raise Exception('No open file for path: %s', path)
        node = h5f[path]
        if isinstance(node, h5py.Dataset):
            # print 'Warning - removing the 0 th element from data array as it is spurious in MOOSE table'
            return node

    # I have a little problem here - how do we find nodes by regular
    # expression for arbitrary file structure?
    #
    # This is not trivial to solve and will need writing a dfa in
    # python. Looks like an overkill. So do it the stupid way.
    
    def getDataByRe(self, pattern):
        """Select data items based on pattern.

        Currently this will do just a regular expression match. It
        checks through all the currently selected files.

        """
        try:
            regex = re.compile(pattern)
        except TypeError, e:
            print e
            print 'Received:', type(pattern), ': "', pattern, '"'
            return
        ret = {}
        for item in self.selectedItems():
            current = item
            parent = current.parent()
            while current.parent() != None:
                current = parent
                parent = current.parent()
            filename = str(current.text(0))
            filehandle = self.fhandles[filename]
            path = item.path()
            if current != item:
                current_node = filehandle[path[len(filename)+1:]]
            else:
                current_node = filehandle
            def check_n_select(name, obj):
                if isinstance(obj, h5py.Dataset) and (str(obj.name).find('ectopic_') < 0) and regex.match(str(obj.name)):
                    table_path = path + '/' + name
                    ret[table_path] = obj
                return None
            if isinstance(current_node, h5py.Group):
                current_node.visititems(check_n_select)
        return ret
                
    def getAttribute(self, path, attribute=None):
        h5f = None
        ret = None
        filename = self.getOpenFileName(path)
        try:
            h5f = self.fhandles[filename]
        except KeyError:
            return None
        if path != filename:
            path = path[len(filename)+1:] # 1 for '/'
            node = h5f[path]        
        else:
            node = h5f
            
        if (attribute is not None) and isinstance(attribute, str):
            try:
                ret = node.attrs[attribute]
            except KeyError:
                ret = None
        else:
            ret = node.attrs
        return ret


    def getOpenFileName(self, path):
        """Added this little function to avoid repetition.  It returns
        the filename part of a selected HDF5 path.
        """
        for key, value in self.fhandles.items():
            if path.startswith(key):
                return key
        return None
    
    def getTimeSeries(self, path):
        h5f = self.fhandles[self.getOpenFileName(path)]
        scheduling = h5f.get('/runconfig/scheduling')
        if scheduling is not None:
            for item in scheduling:
                if item[0] == 'simtime':
                    simtime = float(item[1])
                if item[0] == 'plotdt':
                    plotdt = float(item[1])
        else:
            try:
                simtime = h5f.attrs['simtime']
                plotdt = h5f.attrs['plotdt']
            except KeyError:
                simtime = None
                plotdt = 1.0
        data = self.getData(path)
        num_points = len(data)
        if simtime is not None:
            ret = numpy.linspace(0, simtime, num_points)
        else:
            ret = numpy.linspace(0, num_points, 1)
        return ret

    def get_plotdt(self, path):
        h5f = self.fhandles[self.getOpenFileName(path)]
        scheduling = h5f.get('/runconfig/scheduling')
        if scheduling is not None:
            for item in scheduling:
                if item[0] == 'plotdt':
                    return float(item[1])
        else:
            return h5f.attrs['plotdt']

    def get_simtime(self, path):
        h5f = self.fhandles[self.getOpenFileName(path)]
        scheduling = h5f.get('/runconfig/scheduling')
        if scheduling is not None:
            for item in scheduling:
                if item[0] == 'simtime':
                    return float(item[1])
        else:
            return h5f.attrs['simtime']
        

    def saveSelectedDataToCsvFile(self, filename):
        """Save the data for selected nodes into text file"""
        data_list = []
        headers = []
        paths = []
        print 'Fields in file:'
        for item in self.selectedItems():
            if isinstance(item.h5node, h5py.Dataset):
                # Avoid the spurious 0-th entry in MOOSE table
                data_list.append(numpy.zeros(len(item.h5node)-1))
                data_list[-1][:] = item.h5node[1:]
                headers.append(item.h5node.name)
                paths.append(item.path())
                print paths[-1]
        if data_list:
            length = len(data_list[0])            
            print 'Number of datapoints', length
            array_to_save = numpy.zeros((length, len(data_list)+1))
            array_to_save[:,0] = self.getTimeSeries(paths[0])[:]
            for ii in range(len(data_list)): 
                assert(len(data_list[ii]) == length)                
                array_to_save[:, ii+1] = data_list[ii][:]
            print 'Array shape:', array_to_save.shape
        numpy.savetxt(filename, array_to_save)
        print 'Saved', paths, 'to', filename
                

    def closeCurrentFile(self):
        to_delete = {}
        for item in self.selectedItems():
            filename = self.getOpenFileName(item.path())
            try:
                fhandle = self.fhandles[filename]
                fhandle.close()
                del self.fhandles[filename]
            except KeyError:
                print 'File not open:', filename
            current = item
            parent = current.parent()
            while current.parent() != None:
                current = parent
                parent = current.parent()
            to_delete[current] = 1
        for item in to_delete.keys():
            index = self.indexOfTopLevelItem(item)
            self.takeTopLevelItem(index)
            del item

    def __del__(self):
        for filename, fhandle in self.fhandles.items():
            fhandle.close()
            
if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    QtGui.qApp = app
    # mainwin = DataVizGui()
    mainwin = QtGui.QMainWindow()
    tree = H5TreeWidget(mainwin)    
    tree.addH5Handle('../py/data/data_20110215_112900_1335.h5')
    mainwin.setCentralWidget(tree)
    mainwin.show()
    app.exec_()
                


# 
# hdftree.py ends here

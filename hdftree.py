# hdftree.py --- 
# 
# Filename: hdftree.py
# Description: 
# Author: Subhasis Ray
# Maintainer: 
# Copyright (C) 2010 Subhasis Ray, all rights reserved.
# Created: Fri Mar  4 17:54:30 2011 (+0530)
# Version: 
# Last-Updated: Fri Mar  4 17:55:35 2011 (+0530)
#           By: Subhasis Ray
#     Update #: 3
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
import h5py
from PyQt4 import Qt, QtCore, QtGui

class H5Handle:
    """Generic handler for hdf5 files.
    
    """    
    def __init__(self, filename, mode='r'):
        self.file = h5py.File(filename, mode)

    def getNode(self, path):
        tokens = path.split('/')
        current = self.file
        for element in tokens:
            current = current[element]
        return current
        
    def getArray(self, path):
        node = self.getNode(path)
        if isinstance(node, h5py.DataSet):
            return numpy.array(node)

    def __del__(self):
        self.file.close()

class H5TreeWidgetItem(QtGui.QTreeWidgetItem):
    def __init__(self, parent, h5node):
        QtGui.QTreeWidgetItem.__init__(self, parent)
        self.h5node = h5node
        if isinstance(h5node, h5py.File):
            self.setText(0, QtCore.QString(h5node.filename))
        else:
            self.setText(0, QtCore.QString(h5node))

    def childCount(self):
        ret = len(self.h5node)
        print ret
        return ret

    def hasChildren(self, index):
        ret = (len(self.h5node) > 0)
        print ret
        return ret
    
    def index(self):
        print 'here'
        QtCore.qDebug('Here')

class H5TreeWidget(QtGui.QTreeWidget):
    def __init__(self, *args):
        QtGui.QTreeWidget.__init__(self, *args)
        self.fhandles = []
        
    def addH5Handle(self, handle):
        if not handle in self.fhandles:
            self.fhandles.append(handle)
            item = H5TreeWidgetItem(self, handle)
            self.addTopLevelItem(item)
            item.setText(0, QtCore.QString(handle.filename))
            self.addTree(item, handle)
            
    def addTree(self, currentItem, node):
        if isinstance(node, h5py.Group) or isinstance(node, h5py.File):
            for child in node:
                item = H5TreeWidgetItem(currentItem, child)
                self.addTree(item, node[child])


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    QtGui.qApp = app
    # mainwin = DataVizGui()
    mainwin = QtGui.QMainWindow()
    handle = h5py.File('data/data_20110215_112900_1335.h5', 'r')
    tree = H5TreeWidget(mainwin)    
    tree.addH5Handle(handle)
    mainwin.setCentralWidget(tree)
    mainwin.show()
    app.exec_()
                


# 
# hdftree.py ends here

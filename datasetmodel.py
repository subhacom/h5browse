# datasetmodel.py --- 
# 
# Filename: datasetmodel.py
# Description: 
# Author: Subhasis Ray
# Maintainer: 
# Created: Wed May 16 10:57:05 2012 (+0530)
# Version: 
# Last-Updated: Tue Dec 25 15:34:00 2012 (+0530)
#           By: subha
#     Update #: 264
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

import numpy
import h5py
from PyQt4 import QtGui, QtCore, Qt

class HDFDatasetModel(QtCore.QAbstractTableModel):
    """Custom data mode for interfacing to large datasets in HDF5.
    
    2012-12-25: removing the caching because h5py alreadt does that.

    """
    def __init__(self, *args, **kwargs):
        QtCore.QAbstractTableModel.__init__(self, *args, **kwargs)

    def setDataset(self, node):
        self._dset = numpy.asarray(node)
        
    def data(self, index, role):
        if role != Qt.Qt.DisplayRole:
            return QtCore.QVariant()
        if not index.isValid():
            return QtCore.QVariant()
        row = index.row()
        if row < 0 or row >= self._dset.shape[0]:
            return QtCore.QVariant()
        colcnt = self.columnCount(QtCore.QModelIndex())
        if index.column() >= colcnt or colcnt < 1:
            return QtCore.QVariant()
        elif colcnt == 1:
            _data = self._dset[row]
        elif colcnt > 1:            
            _data = self._dset[row][index.column()]
        return QtCore.QVariant(str(_data))

    def headerData(self, section, orientation, role):
        if role != Qt.Qt.DisplayRole:
            return QtCore.QVariant()
        if orientation == Qt.Qt.Vertical:
            return section
        dtype = self._dset.dtype
        if (dtype.names is not None) and (section < len(dtype.names)):
            return QtCore.QVariant(dtype.names[section])
        print
        return section
        
    def rowCount(self, modelIndex):
        if not self._dset.shape:
            return 0
        return self._dset.shape[0]

    def columnCount(self, modelIndex):
        if not self._dset.shape:
            return 0
        if self._dset.dtype.names is not None:
            return len(self._dset.dtype.names)
        if len(self._dset.shape) == 1:
            return 1
        return self._dset.shape[1]

    def sort(self, ncol, order):
        self.emit(QtCore.SIGNAL('layoutAboutToBeChanged()'))
        field=None
        if self._dset.dtype.names:
            field = self._dset.dtype.names[ncol]
        self._dset.sort(order=field)
        if order == Qt.Qt.DescendingOrder:
            self._dset = self._dset[::-1]
        self.emit(QtCore.SIGNAL('layoutChanged()'))
    
def test_main():
    app = QtGui.QApplication([])
    main = QtGui.QMainWindow()
    tabview = QtGui.QTableView(main)
    fd = h5py.File('test_data/network_20111025_115951_4849.h5')
    dset = fd['/network/cellnetwork/gnmda']
    dset2 = fd['/network/celltype']
    model = HDFDatasetModel()
    model.setDataset(dset)
    tabview.setModel(model)
    model2 = HDFDatasetModel()
    model2.setDataset(dset2)
    tabview2 = QtGui.QTableView(main)
    tabview2.setModel(model2)
    widget = QtGui.QWidget(main)
    widget.setLayout(QtGui.QHBoxLayout())
    widget.layout().addWidget(tabview)
    widget.layout().addWidget(tabview2)
    main.setCentralWidget(widget)
    main.show()
    app.exec_()

if __name__ == '__main__':
    test_main()

# 
# datasetmodel.py ends here

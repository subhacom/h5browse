# hdfdatasetmodel.py --- 
# 
# Filename: hdfdatasetmodel.py
# Description: 
# Author: subha
# Maintainer: 
# Created: Fri Jul 24 01:52:26 2015 (-0400)
# Version: 
# Last-Updated: Thu Sep 17 15:17:37 2015 (-0400)
#           By: Subhasis Ray
#     Update #: 445
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
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; see the file COPYING.  If not, write to
# the Free Software Foundation, Inc., 51 Franklin Street, Fifth
# Floor, Boston, MA 02110-1301, USA.
# 
# 

# Code:
"""Models for HDF5 datasets"""

import h5py as h5
from pyqtgraph import QtCore


def datasetType(dataset):
    if len(dataset.shape) == 0:
        return 'scalar'
    elif len(dataset.shape) == 1:
        if dataset.dtype.names is not None:
            return 'compound'
        else:
            return '1d'
    elif len(dataset.shape) == 2:
        return '2d'
    else:
        return 'nd'


class HDFDatasetModel(QtCore.QAbstractTableModel):
    def __init__(self, dataset, parent=None):
        super(HDFDatasetModel, self).__init__(parent=parent)
        self.dataset = dataset

    def rowCount(self, index):
        raise NotImplementedError('This must be implemented in subclass')

    def columnCount(self, index):
        raise NotImplementedError('This must be implemented in subclass')

    def extractDataType(self, data):
        typename = type(data).__name__
        if isinstance(data, h5.Reference):            
            if data.typecode == 0:
                data = 'ObjectRef({})'.format(self.dataset.file[data].name)
                typename = 'ObjectReference'
            else:
                data = 'RegionRef({})'.format(self.dataset.file[data].name)
                typename = 'RegionReference'
        return data, typename

 
class ScalarDatasetModel(HDFDatasetModel):
    def __init__(self, dataset, parent=None):
        super(ScalarDatasetModel, self).__init__(dataset, parent)
    
    def rowCount(self, index):
        return 1

    def columnCount(self, index):
        return 1

    def data(self, index, role):
        if (role != QtCore.Qt.DisplayRole and role != QtCore.Qt.ToolTipRole) \
           or (not index.isValid()):
            return None
        _data = self.dataset[()] # scalar data
        _data, typename = self.extractDataType(_data)
        if role == QtCore.Qt.ToolTipRole:
            return typename
        return str(_data)
   
    def rawData(self, index=None):
        return self.dataset[()]

    def headerData(self, section, orientation, role):
        if role != QtCore.Qt.DisplayRole:
            return None
        return section


class OneDDatasetModel(HDFDatasetModel):
    def __init__(self, dataset, parent=None):
        super(OneDDatasetModel, self).__init__(dataset, parent)

    def rowCount(self, index):
        return self.dataset.shape[0]

    def columnCount(self, index):
        return 1

    def headerData(self, section, orientation, role):
        if role != QtCore.Qt.DisplayRole:
            return None
        return section

    def data(self, index, role):
        if (role != QtCore.Qt.DisplayRole and role != QtCore.Qt.ToolTipRole) \
           or (not index.isValid())  \
           or (index.row() > self.dataset.shape[0]):
            return None
        _data = self.dataset[index.row()]
        _data, typename = self.extractDataType(_data)
        if role == QtCore.Qt.ToolTipRole:
            return typename
        return str(_data)

    def rawData(self, index=None):
        """Select raw data from dataset as numpy array"""
        if index is None:
            return np.asarray(self.dataset)
        return self.dataset[index]


class CompoundDatasetModel(HDFDatasetModel):
    def __init__(self, dataset, parent=None):
        super(CompoundDatasetModel, self).__init__(dataset, parent)

    def rowCount(self, index):
        return self.dataset.shape[0]

    def columnCount(self, index):
        return len(self.dataset.dtype.names)

    def headerData(self, section, orientation, role):
        if role != QtCore.Qt.DisplayRole:
            return None
        if orientation == QtCore.Qt.Vertical:
            return section
        names = self.dataset.dtype.names
        if names != None and section < len(names):
            return names[section]
        return section

    def data(self, index, role):
        if (role != QtCore.Qt.DisplayRole and role != QtCore.Qt.ToolTipRole) \
           or (not index.isValid()):
            return None
        colname = self.dataset.dtype.names[index.column()]
        _data = self.dataset[colname][index.row()]
        _data, typename = self.extractDataType(_data)
        if role == QtCore.Qt.ToolTipRole:
            return typename
        return str(_data)

    def rawData(self, index=None):
        if index is None:
            return np.asarray(self.dataset)
        return self.dataset[index]


class TwoDDatasetModel(HDFDatasetModel):
    def __init__(self, dataset, parent=None):
        super(TwoDDatasetModel, self).__init__(dataset, parent)

    def rowCount(self, index):
        return self.dataset.shape[0]

    def columnCount(self, index):
        return self.dataset.shape[1]

    def headerData(self, section, orientation, role):
        if role != QtCore.Qt.DisplayRole:
            return None
        return section

    def data(self, index, role):
        if (role != QtCore.Qt.DisplayRole and role != QtCore.Qt.ToolTipRole) \
           or (not index.isValid())  \
           or (index.row() > self.dataset.shape[0]) \
           or (index.column() > self.dataset.shape[1]):
            return None
        _data = self.dataset[index.row(), index.column()]
        _data, typename = self.extractDataType(_data)
        if role == QtCore.Qt.ToolTipRole:
            return typename
        return str(_data)

    def rawData(self, index=None):
        """Select raw data from dataset as numpy array"""
        if index is None:
            return np.asarray(self.dataset)
        return self.dataset[index]


# Create a subclass for 2D view of N-D datasets to separate the logic
# from 1D and 2D datasets, which are expected to be more common. In
# case of views into an HDF5 dataset, temporary arrays are created by
# h5py according to the documentation (as of Fri Jul 31 20:29:50 EDT
# 2015). We want to avoid that performance penalty for the common
# case.

class NDDatasetModel(HDFDatasetModel):
    """2D projection of N-D dataset. It uses numpy advanced
    slicing/indexing via tuples.

    `pos` should be a tuple containing integer indices along all
    dimensions except the ones to be included entirely. The string '*'
    should be placed for the latter.  Thus (1, 1, '*', 1, '*') on a 5D
    dataset will select the third and the fifth dimension (counting
    from 1).

    The argiments should come from user input (a popout dialog).

    """
    def __init__(self, dataset, parent=None, pos=()):
        super(NDDatasetModel, self).__init__(dataset, parent=parent)
        self.select2D(pos)
        
    def rowCount(self, index):
        return self.data2D.shape[0]

    def columnCount(self, index):
        return self.data2D.shape[1]

    def headerData(self, section, orientation, role):
        if role != QtCore.Qt.DisplayRole:
            return None
        return section

    def data(self, index, role):
        if (role != QtCore.Qt.DisplayRole and role != QtCore.Qt.ToolTipRole) or (not index.isValid()) \
           or index.row() < 0 or index.row() > self.data2D.shape[0]:
            return None
        _data = self.data2D[index.row(), index.column()]
        _data, typename = self.extractDataType(_data)
        if role == QtCore.Qt.ToolTipRole:
            return typename
        return str(_data)

    def select2D(self, pos):
        """Select data for specified indices on each dimension except the two
        to be displayed in their entirety.
        
        pos : a sequence of integers specifying the indices on each
        dimension except the row and column dimensions for display,
        which should be '*'. If the number of entries is less than the
        dimensions of the dataset, 0 is taken for the missing ones. If
        more, the trailing ones are ignored.

        Thus pos=(1, 1, '*', 1, '*') on a 5D dataset will select the
        third and the fifth dimension (counting from 1).

        """
        pos = list(pos)
        if len(pos) < 2: # too few positions, include XY
            pos = [slice(0, self.dataset.shape[0]),
                   slice(0, self.dataset.shape[1])] #! why access shape[1] before verifying 
        indices = []        
        ndim = len(self.dataset.shape)  # h5py does not implement ndim attribute for datasets
        if ndim < len(pos):
            pos = pos[:ndim]
        elif ndim > len(pos):
            pos += [0] * (ndim - len(pos))
        for idx, dimsize in zip(pos, self.dataset.shape):
            if isinstance(idx, int):
                indices.append(idx)
            else:
                indices.append(slice(0, dimsize))
        self.indices = tuple(indices)
        self.data2D = self.dataset[self.indices]

    def rawData(self, index=None):
        if index is None:
            return self.data2D
        return self.dataset[index]


def create_default_model(dataset, parent=None, pos=()):
    """Create a model suitable for a given HDF5 dataset.
    
    For multidimensional homogeneous datasets it defaults to the first
    two dimensions and 0-th entry for the rest of the dimensions

    """
    dsetType = datasetType(dataset)
    if dsetType == 'scalar':
        return ScalarDatasetModel(dataset, parent=parent)
    elif dsetType == 'compound':
        return CompoundDatasetModel(dataset, parent=parent)
    elif dsetType == '1d':
        return OneDDatasetModel(dataset, parent=parent)
    elif dsetType == '2d':
        return TwoDDatasetModel(dataset, parent=parent)
    else:
        return NDDatasetModel(dataset, parent=parent, pos=())
        

from pyqtgraph import QtGui    

if __name__ == '__main__':
    import sys
    app = QtGui.QApplication(sys.argv)
    window = QtGui.QMainWindow()
    tabview = QtGui.QTableView(window)
    fd = h5.File('poolroom.h5', 'r')
    model = create_default_model(fd['/map/nonuniform/tables/players'])
    # tabview.setModel(model)
    # model2 = create_default_model(fd['/data/uniform/ndim/data3d'], pos=('*', 1, '*'))
    # tabview2 = QtGui.QTableView(window)
    # tabview2.setModel(model2)
    # model3 = create_default_model(fd['/data/uniform/balls/x'])
    # tabview3 = QtGui.QTableView(window)
    # tabview3.setModel(model3)
    # widget = QtGui.QWidget(window)
    # widget.setLayout(QtGui.QHBoxLayout())
    # widget.layout().addWidget(tabview)
    # widget.layout().addWidget(tabview2)
    # widget.layout().addWidget(tabview3)
    # window.setCentralWidget(widget)
    # window.show()
    sys.exit(app.exec_())



# 
# hdfdatasetmodel.py ends here

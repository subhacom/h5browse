# hdfdatasetmodel.py --- 
# 
# Filename: hdfdatasetmodel.py
# Description: 
# Author: subha
# Maintainer: 
# Created: Fri Jul 24 01:52:26 2015 (-0400)
# Version: 
# Last-Updated: Mon Aug  3 23:46:53 2015 (-0400)
#           By: subha
#     Update #: 253
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
from PyQt5.QtCore import (QAbstractTableModel, QItemSelectionModel, QModelIndex, Qt)


class HDFDatasetModel(QAbstractTableModel):
    def __init__(self, dataset, parent=None):
        super().__init__(parent)
        self.dataset = dataset
        

    def rowCount(self, index):
        if len(self.dataset.shape) == 0:
            return 1
        return self.dataset.shape[0]

    def columnCount(self, index):
        if len(self.dataset.shape) == 0:
            return 1
        # Handle compound datasets. 
        # We are assuming only one-column compound dataset.
        if self.dataset.dtype.names is not None:
            return len(self.dataset.dtype.names)
        # 1D dataset
        if len(self.dataset.shape) == 1:
            return 1
        return self.dataset.shape[1]

    def headerData(self, section, orientation, role):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Vertical:
            return section
        names = self.dataset.dtype.names
        if names != None and section < len(names):
            return names[section]
        return section

    def data(self, index, role):
        if role != Qt.DisplayRole or (not index.isValid()) \
           or index.row() < 0 or index.row() >self.dataset.shape[0]:
            return None
        colcnt = self.columnCount(QModelIndex())
        names = self.dataset.dtype.names
        if names is not None:
            _data = self.dataset[names[index.column()]][index.row()]
        elif index.column() >= colcnt or colcnt < 1:
            return None
            
        elif (colcnt == 1):
            if (len(self.dataset.shape) > 0):
                _data = self.dataset[index.row()]            
            else:
                _data = self.dataset[()] # scalar data
        else:
            _data = self.dataset[index.row()][index.column()]
        # TODO: provide better representation of HDF object data -
        # like object refs.
        return str(_data)


# Create a subclass for 2D view of N-D datasets to separate the logic
# from 1D and 2D datasets, which are expected to be more common. In
# case of views into an HDF5 dataset, temporary arrays are created by
# h5py according to the documentation (as of Fri Jul 31 20:29:50 EDT
# 2015). We want to avoid that performance penalty for the common
# case.

class HDFDatasetNDModel(HDFDatasetModel):
    """2D projection of N-D dataset. It uses numpy advanced
    slicing/indexing via tuples.

    `pos` should be a tuple containing integer indices along all
    dimensions except the ones to be included entirely. The string '*'
    should be placed for the latter.  Thus (1, 1, '*', 1, '*') on a 5D
    dataset will select the third and the fifth dimension (counting
    from 1).

    The argiments should come from user input (a popout dialog).

    """
    def __init__(self, dataset, pos=(), parent=None):
        super().__init__(dataset, parent)
        self.select2D(pos)
        
    def rowCount(self, index):
        if len(self.data2D.shape) == 0:
            return 0
        return self.data2D.shape[0]

    def columnCount(self, index):
        if len(self.data2D.shape) == 0:
            return 0
        # 1D dataset
        if len(self.data2D.shape) == 1:
            return 1
        return self.data2D.shape[1]

    def headerData(self, section, orientation, role):
        if role != Qt.DisplayRole:
            return None
        return section

    def data(self, index, role):
        if role != Qt.DisplayRole or (not index.isValid()) \
           or index.row() < 0 or index.row() >self.data2D.shape[0]:
            return None
        return str(self.data2D[index.row(), index.column()])

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
                   slice(0, self.dataset.shape[1])]
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


def create_default_model(dataset, parent=None):
    """Create a model suitable for a given HDF5 dataset.
    
    For multidimensional homogeneous datasets it defaults to the first
    two dimensions and 0-th entry for the rest of the dimensions

    """
    if len(dataset.shape) <= 2:
        return HDFDatasetModel(dataset, parent)
    else:
        return HDFDatasetNDModel(dataset, pos=(), parent=parent)
        
    

if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import (QApplication, QMainWindow, QHBoxLayout, QTreeView, QWidget, QTableView)
    app = QApplication(sys.argv)
    window = QMainWindow()
    tabview = QTableView(window)
    fd = h5.File('poolroom.h5')
    model = HDFDatasetModel(fd['/map/nonuniform/tables/players'])
    tabview.setModel(model)
    model2 = HDFDatasetNDModel(fd['/data/uniform/ndim/data3d'], ('*', 1, '*'))
    tabview2 = QTableView(window)
    tabview2.setModel(model2)
    model3 = HDFDatasetModel(fd['/data/uniform/balls/x'])
    tabview3 = QTableView(window)
    tabview3.setModel(model3)
    widget = QWidget(window)
    widget.setLayout(QHBoxLayout())
    widget.layout().addWidget(tabview)
    widget.layout().addWidget(tabview2)
    widget.layout().addWidget(tabview3)
    window.setCentralWidget(widget)
    window.show()
    sys.exit(app.exec_())



# 
# hdfdatasetmodel.py ends here

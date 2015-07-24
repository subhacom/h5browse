# hdfdatasetmodel.py --- 
# 
# Filename: hdfdatasetmodel.py
# Description: 
# Author: subha
# Maintainer: 
# Created: Fri Jul 24 01:52:26 2015 (-0400)
# Version: 
# Last-Updated: Fri Jul 24 04:28:57 2015 (-0400)
#           By: subha
#     Update #: 173
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
        super(QAbstractTableModel, self).__init__(parent)
        self.dataset = dataset

    def rowCount(self, index):
        if len(self.dataset.shape) == 0:
            return 0
        return self.dataset.shape[0]

    def columnCount(self, index):
        if len(self.dataset.shape) == 0:
            return 0
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
        elif colcnt == 1:
            _data = self.dataset[index.row()]            
        else:
            _data = self.dataset[index.row()][index.column()]
        return str(_data)


class HDFDatasetNDModel(HDFDatasetModel):
    """2D projection of N-D dataset. It uses numpy advanced
    slicing/indexing via tuples.

    dims should be a tuple containing integer indices along all
    dimensions except the ones to be included entirely. The string '*'
    should be placed for the latter.  Thus (1, 1, '*', 1, '*') on a 5D
    dataset will select the third and the fifth dimension (counting
    from 1).

    The argiments should come from user input (a popout dialog).

    """
    def __init__(self, dataset, dims, parent=None):
        HDFDatasetModel.__init__(self, dataset, parent)
        indices = []
        for ii, idx in enumerate(dims):
            if isinstance(idx, int):
                indices.append(idx)
            else:
                indices.append(slice(0, dataset.shape[ii]))
        self.indices = tuple(indices)
        self.selectedData = self.dataset[self.indices]

    def rowCount(self, index):
        if len(self.selectedData.shape) == 0:
            return 0
        return self.selectedData.shape[0]

    def columnCount(self, index):
        if len(self.selectedData.shape) == 0:
            return 0
        # 1D dataset
        if len(self.selectedData.shape) == 1:
            return 1
        return self.selectedData.shape[1]

    def headerData(self, section, orientation, role):
        if role != Qt.DisplayRole:
            return None
        return section

    def data(self, index, role):
        if role != Qt.DisplayRole or (not index.isValid()) \
           or index.row() < 0 or index.row() >self.selectedData.shape[0]:
            return None
        return str(self.selectedData[index.row(), index.column()])


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

# hdfattributemodel.py --- 
# 
# Filename: hdfattributemodel.py
# Description: 
# Author: subha
# Maintainer: 
# Created: Fri Jul 31 20:48:19 2015 (-0400)
# Version: 
# Last-Updated: Fri Jul 31 22:08:23 2015 (-0400)
#           By: subha
#     Update #: 73
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

import numpy as np
from PyQt5.QtCore import (QAbstractTableModel, QItemSelectionModel, QModelIndex, Qt)

class HDFAttributeModel(QAbstractTableModel):
    """Model class to handle HDF5 attributes of an HDF5 object"""
    def __init__(self, node, parent=None):
        """`node` is an HDF5 object"""
        super().__init__(parent=parent)
        self.node = node
        
    def rowCount(self, index):
        return len(self.node.attrs)

    def columnCount(self, index):
        return 2

    def headerData(self, section, orientation, role):        
        if role != Qt.DisplayRole or orientation == Qt.Vertical:
            return None
        if section == 0:
            return 'Name'
        elif section == 1:
            return 'Value'
        return section

    def data(self, index, role):
        """For tooltips return the data type of the attribute value.  For
        display role, return attribute name (key)for column 0 and
        value for column 1.

        """
        if not index.isValid():
            return None                
        if role == Qt.ToolTipRole:
            attr = list(self.node.attrs.values())[index.row()]
            if isinstance(attr, bytes) or isinstance(attr, str):
                return 'string: scalar'
            if isinstance(attr, np.ndarray):
                return '{}: {}'.format(attr.dtype, attr.shape)
            return '{}: scalar'.format(type(attr).__name__)
        elif role == Qt.DisplayRole:
            if index.column() == 0:
                return list(self.node.attrs.keys())[index.row()]
            elif index.column() == 1:
                attr =list(self.node.attrs.values())[index.row()]
                # in Python 3 we have to decode the bytes to get
                # string representation without leading 'b'
                if isinstance(attr, bytes):
                    return attr.decode('utf-8')
                return str(attr)                
        return None


if __name__ == '__main__':
    import sys
    import h5py as h5
    from PyQt5.QtWidgets import (QApplication, QMainWindow, QHBoxLayout, QTreeView, QWidget, QTableView)
    app = QApplication(sys.argv)
    window = QMainWindow()
    tabview = QTableView(window)
    fd = h5.File('poolroom.h5')
    model = HDFAttributeModel(fd)
    tabview.setModel(model)
    widget = QWidget(window)
    widget.setLayout(QHBoxLayout())
    widget.layout().addWidget(tabview)
    window.setCentralWidget(widget)
    window.show()
    sys.exit(app.exec_())


# 
# hdfattributemodel.py ends here

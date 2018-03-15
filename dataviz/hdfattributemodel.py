# hdfattributemodel.py --- 
# 
# Filename: hdfattributemodel.py
# Description: 
# Author: subha
# Maintainer: 
# Created: Fri Jul 31 20:48:19 2015 (-0400)
# Version: 
# Last-Updated: Thu Mar 15 14:19:27 2018 (-0400)
#           By: Subhasis Ray
#     Update #: 215
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
import h5py as h5
from pyqtgraph import (QtCore, QtGui)

class HDFAttributeModel(QtCore.QAbstractTableModel):
    """Model class to handle HDF5 attributes of an HDF5 object"""
    columns = ['Attribute name', 'Value', 'Type']
    def __init__(self, node, parent=None):
        """`node` is an HDF5 object"""
        super(HDFAttributeModel, self).__init__(parent=parent)
        self.node = node
        
    def rowCount(self, index):
        return len(self.node.attrs)

    def columnCount(self, index):
        return len(HDFAttributeModel.columns)

    def headerData(self, section, orientation, role):        
        if role != QtCore.Qt.DisplayRole or orientation == QtCore.Qt.Vertical:
            return None
        return HDFAttributeModel.columns[section]

    def data(self, index, role):
        """For tooltips return the data type of the attribute value.  For
        display role, return attribute name (key)for column 0 and
        value for column 1.

        """
        if (not index.isValid()) or \
           (role not in (QtCore.Qt.ToolTipRole, QtCore.Qt.DisplayRole)):
            return None              
        for ii, name in enumerate(self.node.attrs):
            if ii == index.row():
                break
        if role == QtCore.Qt.DisplayRole and index.column() == 0:
            return name
        value = None
        try:
            value = self.node.attrs[name]
        except (OSError, IOError) as e:
            value = '<ERROR>'
            print(e)
        if role == QtCore.Qt.DisplayRole:
            if index.column() == 1:                
                if isinstance(value, bytes) or isinstance(value, np.string_):
                    return value.decode()
                elif isinstance(value, np.ndarray) and value.dtype.type == np.string_:
                    return str([entry.decode() for entry in value])                    
                return str(value)
            elif index.column() == 2:
                tinfo = type(value).__name__
                if isinstance(value, np.ndarray): 
                    tinfo += ' of {}'.format(value.dtype)
                return tinfo
        elif role == QtCore.Qt.ToolTipRole:
            if isinstance(value, np.ndarray):
                return '{}: {}'.format(value.dtype, value.shape)
            elif isinstance(value, h5.Reference):
                if value.typecode == 0:
                    return 'ObjectRef: {}'.format(aid.shape)
                else:
                    return 'RegionRef: {}'.format(aid.shape)
            if value is not None:
                return '{}'.format(type(value).__name__)
            return '{}: {}'.format(aid.dtype.name, aid.shape)
        return None


if __name__ == '__main__':
    import sys
    import h5py as h5
    app = QtGui.QApplication(sys.argv)
    window = QtGui.QMainWindow()
    tabview = QtGui.QTableView(window)
    fd = h5.File('poolroom.h5')
    model = HDFAttributeModel(fd)
    tabview.setModel(model)
    widget = QtGui.QWidget(window)
    widget.setLayout(QtGui.QHBoxLayout())
    widget.layout().addWidget(tabview)
    window.setCentralWidget(widget)
    window.show()
    sys.exit(app.exec_())


# 
# hdfattributemodel.py ends here

# hdfattributemodel.py --- 
# 
# Filename: hdfattributemodel.py
# Description: 
# Author: subha
# Maintainer: 
# Created: Fri Jul 31 20:48:19 2015 (-0400)
# Version: 
# Last-Updated: Mon Dec 21 00:48:12 2015 (-0500)
#           By: subha
#     Update #: 191
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
            # try:
            #     ainfo = h5.h5a.get_info(self.node.id, name)
            # if ainfo.data_size == 0:  # empty attribute - not supported by h5py
                # value = '<empty>'
            ## This does not work - unfortunately
            # else:  # a hack to get around unicode issue in h5py
            #     attr = h5.h5a.open(self.node.id, name)
            #     buf = np.ndarray(attr.shape, dtype=attr.dtype)
            #     attr.read(buf)
            #     return buf
        if role == QtCore.Qt.DisplayRole:
            if index.column() == 1:                
                # in Python 3 we have to decode the bytes to get
                # string representation without leading 'b'. However,
                # on second thought, it is not worth converting the
                # strings - for large datasets it will be slow, and if
                # we do the conversion for attributes but not for
                # datasets it gets confusing for the user.
                if value == None:
                    value = '<Could not read>'
                return str(value)
                
                # if isinstance(value, bytes):
                #     return value.decode('utf-8')
                # elif isinstance(value, np.ndarray) and value.dtype.type == np.string_:
                #     return str([entry.decode('utf-8') for entry in value])                    
                # return str(value)                
            elif index.column() == 2:
                if value is not None:
                    return type(value).__name__
                aid = h5.h5a.open(self.node.id, name)
                return aid.dtype.name
        elif role == QtCore.Qt.ToolTipRole:
            # if isinstance(value, bytes) or isinstance(value, str):
            #     return 'string: scalar'            
            if isinstance(value, np.ndarray):
                return '{}: {}'.format(value.dtype, value.shape)
            elif isinstance(value, h5.Reference):
                if value.typecode == 0:
                    return 'ObjectRef: {}'.format(aid.shape)
                else:
                    return 'RegionRef: {}'.format(aid.shape)
            if value is not None:
                return '{}: {}'.format(type(value).__name__, value.shape)                
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

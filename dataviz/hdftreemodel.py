# hdftreemodel.py --- 
# 
# Filename: hdftreemodel.py
# Description: 
# Author: subha
# Maintainer: 
# Created: Thu Jul 23 22:07:53 2015 (-0400)
# Version: 
# Last-Updated: Sun Sep 20 11:48:00 2015 (-0400)
#           By: subha
#     Update #: 716
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

"""This code borrows heavily from the PyQt5 example:
editabletreemodel.py

- Subhasis Ray, Thu Jul 23 23:40:39 EDT 2015

"""

import os
import h5py as h5
from  pyqtgraph import QtCore
from pyqtgraph import QtGui
from pyqtgraph import Qt

class RootItem(object):
    def __init__(self, parent=None):
        super(RootItem, self).__init__()
        self.parentItem = parent
        self.children = []

    def child(self, row):
        if row < 0 or row >= len(self.children):
            return None
        return self.children[row]
            
    def childCount(self):
        return len(self.children)

    def childNumber(self):
        return 0
        
    def columnCount(self):
        return 1

    def data(self, column, role=QtCore.Qt.DisplayRole):
        if role == QtCore.Qt.DisplayRole:
            return 'Files'
        elif role == QtCore.Qt.ToolTipRole:
            return 'List of open files'

    def setData(self, column, value):
        return False

    def parent(self):
        return self.parentItem

    def addChild(self, childItem):
        self.children.append(childItem)    

    def removeChild(self, position):
        if position < 0 or position > len(self.children):
            return False
        child = self.children.pop(position)
        return True

    def hasChildren(self):
        return len(children) > 0


class HDFTreeItem(object):
    def __init__(self, data, parent=None):
        super(HDFTreeItem, self).__init__()
        self.parentItem = parent
        self.h5node = data
        self.children = []
        
    def child(self, row):
        if isinstance(self.h5node, h5.Group):
            if len(self.children) > 0:
                return self.children[row]                
            for name in self.h5node:
                # __class__ allows this function to work for subclasses as well
                self.children = [self.__class__(child, parent=self) for child in self.h5node.values()]                  
            return self.children[row]

    def childNumber(self):
        return self.parentItem.children.index(self)
        
    def childCount(self):
        if isinstance(self.h5node, h5.Group):
            return len(self.h5node)
        return 0

    def columnCount(self):
        return 1

    def data(self, column, role=QtCore.Qt.DisplayRole):
        if self.h5node == None:
            return ''
        if role == QtCore.Qt.DisplayRole:
            if isinstance(self.h5node, h5.File):
                return os.path.basename(self.h5node.filename)
            return self.h5node.name.rsplit('/')[-1]
        elif role == QtCore.Qt.ToolTipRole:
            if isinstance(self.h5node, h5.File):
                return self.h5node.filename
            shape = ''
            if isinstance(self.h5node, h5.Dataset):
                shape = self.h5node.shape
                if len(shape) == 0:
                    shape = 'scalar'
            return '{} {}'.format(self.h5node.__class__.__name__, shape)

    def setData(self, column, value):
        if column != 0:
            return False
        self.h5node = value

    def hasChildren(self):
        if isinstance(self.h5node, h5.Group):
            return len(self.h5node) > 0
        return False

    def parent(self):
        return self.parentItem

    def isDataset(self):
        return isinstance(self.h5node, h5.Dataset)

    def isFile(self):
        return isinstance(self.h5node, h5.File)

    def isGroup(self):
        return isinstance(self.h5node, h5.Group)


class EditableItem(HDFTreeItem):    
    def __init__(self, data, parent=None):
        super(EditableItem, self).__init__(data, parent)
        
    def setData(self, column, data):
        """When assigned a dict, we look for 'name' key storing name, 'attr'
        key storing attributes of node to be created and 'type' for
        group/dataset. If type is dataset, we further look for any existing
        data in 'data'."""
        if not isinstance(data, dict):
            super().setData(self, column, data)
            return
        typ = data.get('type', 'group')
        merge = data.get('merge', False)
        attrs = data.get('attrs', {})
        if not merge:
            if typ == 'group':
                self.createGroup(data)
            else:
                self.createDataset(data)            
        for key, value in attrs:
            self.h5node.attrs[key] = value        

    def createGroup(self, data):
        name = data.get('name', 'NewGroup')
        group = self.h5node.create_group(name)
        for key, value in data.get('attrs', {}).items():
            group.attrs[key] = value
        self.children.append(EditableItem(group, self))
        
    def createDataset(self, data):
        name = data.get('name', 'NewDataset')
        if self.isDataset():
            parent = self.parent()
        else:
            parent = self
        dset = parent.h5node.create_dataset(name, data=data.get('data', None),
                                            shape=data.get('shape', None),
                                            dtype=data.get('dtype', None),
                                            chunks=data.get('chunks', True),
                                            maxshape=data.get('maxshape', (None,)),
                                            compression=data.get('compression', 'gzip'))
        for key, value in data.get('attrs', {}).items():
            dset.attrs[key] = value
        self.children.append(EditableItem(dset, self))

    def insertChildren(self, position, count, columns=1):
        for ii in range(count):
            name = 'node{}'.format(ii)
            group = self.h5node.create_group(name)
            self.children.append(EditableItem(group, self))
        return True

    def removeChildren(self, position, count):
        index = 0
        for key in self.h5node:
            if index >= position:
                child = self.children.pop(index)
                del self.h5node[key]
            index += 1
            if index >= position + count:
                break

    def removeChild(self, position):
        if position < 0 or position > len(self.children):
            return False
        child = self.removeChildren(position, 1)
        return True

    def rename(self, newName):
        pnode = self.parent().h5node
        pnode.move(self.h5node.name, newName)

        
class HDFTreeModel(QtCore.QAbstractItemModel):
    def __init__(self, headers, parent=None):
        super(HDFTreeModel, self).__init__(parent)
        rootData = [header for header in headers]
        self.rootItem = RootItem() 
        
    def columnCount(self, parent=QtCore.QModelIndex()):
        return self.rootItem.columnCount()

    def data(self, index, role):
        if not index.isValid():
            return None
        item = self.getItem(index)
        return item.data(index.column(), role)

    def getItem(self, index):
        if index.isValid():
            item = index.internalPointer()
            if item:
                return item
        return self.rootItem
        # Strange: if I do not return rootItem as default, nothing shows up

    def flags(self, index):
        if not index.isValid():
            return 0
        return QtCore.Qt.ItemIsEnabled |QtCore.Qt.ItemIsSelectable

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        if orientation == QtCore.Qt.Horizontal:
            return self.rootItem.data(section, role)
        return None

    def index(self, row, column, parent=QtCore.QModelIndex()):
        if parent.isValid() and parent.column()!= 0:
            return QtCore.QModelIndex()
        parentItem = self.getItem(parent)
        if parentItem is None:
            return QtCore.QModelIndex()
        childItem = parentItem.child(row)
        if childItem:
            return self.createIndex(row, column, childItem)
        else:
            return QtCore.QModelIndex()

    def parent(self, index):
        if not index.isValid():
            return QtCore.QModelIndex()        
        childItem = self.getItem(index)
        parentItem = childItem.parent()
        if parentItem == self.rootItem: # is the left side childItem or parentItem?
            return QtCore.QModelIndex()
        return self.createIndex(parentItem.parent().childNumber(), 0, parentItem)

    def rowCount(self, parent=QtCore.QModelIndex()):
        parentItem = self.getItem(parent)
        if parentItem is not None:
            return parentItem.childCount()
        return 0

    def openFile(self, path, mode='r'):
        self.beginInsertRows(QtCore.QModelIndex(),
                             self.rootItem.childCount(),
                             self.rootItem.childCount()+1)
        fd = h5.File(str(path), mode=mode)
        # print('****', fd)
        if mode == 'r':
            fileItem = HDFTreeItem(fd, parent=self.rootItem)
        else:
            fileItem = EditableItem(fd, parent=self.rootItem)
        self.rootItem.addChild(fileItem)
        self.endInsertRows()

    def closeFile(self, index):
        """Close file associated with item at index. Returns True if
        successful, False if the item is not a file item."""
        item = self.getItem(index)
        try:
            position = self.rootItem.children.index(item)
            self.beginRemoveRows(QtCore.QModelIndex(), position, position+1)
            item.h5node.close()
            self.rootItem.removeChild(position)
            self.endRemoveRows()
            return True
        except ValueError:
            return False

    def insertRows(self, position, rows, parent=QtCore.QModelIndex()):
        parentItem = self.getItem(parent)
        self.beginInsertRows(parent, position, position+rows-1)
        parentItem.insertChildren(position, rows, self.rootItem.columnCount())
        self.endInsertRows()
        return True

    def removeRows(self, position, rows, parent=QtCore.QModelIndex()):
        parentItem = self.getItem(parent)
        self.beginRemoveRows(parent, position, position+rows-1)
        parentItem.removeChildren(position, rows, self.rootItem.columnCount())
        self.endRemoveRows()
        return True

    def insertNode(self, parent=QtCore.QModelIndex(), data={}, nodeType=h5.Group):
        parentItem = self.getItem(parent)
        self.beginInsertRows(parent, parentItem.childCount(), parentItem.childCount())
        if nodeType == h5.Dataset:
            parentItem.createDataset(data)
        elif nodeType == h5.Group:
            parentItem.createGroup(data)
        self.endInsertRows()
        return True

    # def insertGroup(self, parent=QtCore.QModelIndex(), data={}):
    #     parentItem = self.getItem(parent)
    #     self.beginInsertRows(parent, parentItem.childCount(), parentItem.childCount())
    #     parentItem.createGroup(data)
    #     self.endInsertRows()
    #     return True

    def deleteNode(self, index):
        item = self.getItem(index)
        parent = item.parent()
        self.beginRemoveRows(index.parent(), index.row(), 1)
        parent.removeChild(index.row())
        self.endRemoveRows()


if __name__ == '__main__':
    import sys
    app = QtGui.QApplication(sys.argv)
    window = QtGui.QMainWindow()
    widget = QtGui.QWidget()
    layout = QtGui.QVBoxLayout(widget)
    view = QtGui.QTreeView(widget)
    layout.addWidget(view)
    window.setCentralWidget(widget)
    model = HDFTreeModel([])
    model.openFile('poolroom.h5', 'r+')
    view.setModel(model)
    window.show()
    sys.exit(app.exec_())
    


# 
# hdftreemodel.py ends here

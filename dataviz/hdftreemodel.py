# hdftreemodel.py --- 
# 
# Filename: hdftreemodel.py
# Description: 
# Author: subha
# Maintainer: 
# Created: Thu Jul 23 22:07:53 2015 (-0400)
# Version: 
# Last-Updated: Sat Aug  1 02:17:52 2015 (-0400)
#           By: subha
#     Update #: 393
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
from PyQt5.QtCore import (QAbstractItemModel, QItemSelectionModel, QModelIndex, Qt)

class RootItem(object):
    def __init__(self, parent=None):
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

    def data(self, column, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            return 'Files'
        elif role == Qt.ToolTipRole:
            return 'List of open files'

    def setData(self, column, value):
        return False

    def parent(self):
        return None

    def appendChild(self, childItem):
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
        self.h5node = data
        self.parentItem = parent
        self.children = []
        if isinstance(self.h5node, h5.Group):
            self.children = [HDFTreeItem(child, self) for child in self.h5node.values()]        
        
    def child(self, row):
        return self.children[row]
            
    def childCount(self):
        if isinstance(self.h5node, h5.Group):
            return len(self.h5node)
        return 0

    def childNumber(self):
        return self.parentItem.children.index(self)

    def columnCount(self):
        return 1

    def data(self, column, role=Qt.DisplayRole):
        if self.h5node == None:
            return ''
        if role == Qt.DisplayRole:
            if isinstance(self.h5node, h5.File):
                return os.path.basename(self.h5node.filename)
            return self.h5node.name.rsplit('/')[-1]
        elif role == Qt.ToolTipRole:
            if isinstance(self.h5node, h5.File):
                return self.h5node.filename
            return '{} : {}'.format(self.h5node.name,
                                    self.h5node.__class__.__name__)

    def setData(self, column, value):
        if column != 0:
            return False
        self.h5node = value

    def parent(self):
        return self.parentItem

    def hasChildren(self):
        if isinstance(self.h5node, h5.Group):
            return len(self.h5node) > 0
        return False
            

class HDFTreeModel(QAbstractItemModel):
    def __init__(self, headers, parent=None):
        super(HDFTreeModel, self).__init__(parent)
        rootData = [header for header in headers]
        self.rootItem = RootItem() 
        
    def columnCount(self, parent=QModelIndex()):
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

    def flags(self, index):
        if not index.isValid():
            return 0
        return Qt.ItemIsEnabled |Qt.ItemIsSelectable

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal:
            return self.rootItem.data(section, role)
        return None

    def index(self, row, column, parent=QModelIndex()):
        if parent.isValid() and parent.column()!= 0:
            return QModelIndex()

        parentItem = self.getItem(parent)
        childItem = parentItem.child(row)
        if childItem:
            return self.createIndex(row, column, childItem)
        else:
            return QModelIndex()

    def parent(self, index):
        if not index.isValid():
            return QModelIndex()
        
        childItem = self.getItem(index)
        parentItem = childItem.parent()

        if parentItem == self.rootItem: # is the left side childItem or parentItem?
            return QModelIndex()

        return self.createIndex(parentItem.childNumber(), 0, parentItem)

    def rowCount(self, parent=QModelIndex()):
        parentItem = self.getItem(parent)
        return parentItem.childCount()

    def openFile(self, path):
        self.beginInsertRows(QModelIndex(),
                             self.rootItem.childCount(),
                             self.rootItem.childCount()+1)
        fd = h5.File(str(path), 'r')
        fileItem = HDFTreeItem(fd, parent=self.rootItem)
        self.rootItem.appendChild(fileItem)
        self.endInsertRows()

    def closeFile(self, index):
        item = self.getItem(index)
        position = self.rootItem.children.index(item)
        if position >= 0:
            self.beginRemoveRows(QModelIndex(), position, position+1)
            item.h5node.close()
            self.rootItem.removeChild(position)
            self.endRemoveRows()


if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QTreeView, QWidget)
    app = QApplication(sys.argv)
    window = QMainWindow()
    widget = QWidget()
    layout = QVBoxLayout(widget)
    view = QTreeView(widget)
    layout.addWidget(view)
    window.setCentralWidget(widget)
    model = HDFTreeModel([])
    model.openFile('poolroom.h5')
    view.setModel(model)
    window.show()
    sys.exit(app.exec_())
    


# 
# hdftreemodel.py ends here

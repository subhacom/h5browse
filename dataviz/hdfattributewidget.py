
# hdfattributewidget.py --- 
# 
# Filename: hdfattributewidget.py
# Description: 
# Author: subha
# Maintainer: 
# Created: Thu Aug  6 21:46:01 2015 (-0400)
# Version: 
# Last-Updated: Thu Sep 17 15:16:45 2015 (-0400)
#           By: Subhasis Ray
#     Update #: 81
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

from pyqtgraph import (QtCore, QtGui)

from hdfattributemodel import HDFAttributeModel

class HDFAttributeWidget(QtGui.QWidget):
    """Convenience widget to display HDF attributes.

    It creates a model when dataset is assigned. Like HDFDatasetWidget
    it assigns filename:nodename.attributes to its `name` field which
    is used by main window to set the window title of this subwindow.

    """
    def __init__(self, parent=None, node=None):
        super(HDFAttributeWidget, self).__init__(parent)        
        self.name = ''
        self.nameLabel = QtGui.QLabel('', self)
        self.nameLabel.setWordWrap(True)
        self.nameLabel.setTextInteractionFlags(QtCore.Qt.TextSelectableByKeyboard | QtCore.Qt.TextSelectableByMouse)
        self.fileLabel = QtGui.QLabel('', self)
        self.fileLabel.setWordWrap(True)
        self.fileLabel.setTextInteractionFlags(QtCore.Qt.TextSelectableByKeyboard | QtCore.Qt.TextSelectableByMouse)
        self.attributeView = QtGui.QTableView(self)
        self.setLayout(QtGui.QVBoxLayout())
        self.layout().addWidget(self.nameLabel)
        self.layout().addWidget(self.fileLabel)
        self.layout().addWidget(self.attributeView)
        if node is not None:
            self.setNode(node)

    def setNode(self, node):
        self.name = 'Attributes: {}'.format(node.name)
        model = HDFAttributeModel(node)
        self.attributeView.setModel(model)
        self.nameLabel.setText('Path: {}'.format(node.name))
        self.fileLabel.setText('File: {}'.format(node.file.filename))
        self.setToolTip('Attributes of <b>{}</b> [file: {}]'.format(node.name, node.file.filename))



# 
# hdfattributewidget.py ends here

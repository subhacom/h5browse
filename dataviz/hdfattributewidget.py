# hdfattributewidget.py --- 
# 
# Filename: hdfattributewidget.py
# Description: 
# Author: subha
# Maintainer: 
# Created: Thu Aug  6 21:46:01 2015 (-0400)
# Version: 
# Last-Updated: Thu Aug 27 00:18:20 2015 (-0400)
#           By: subha
#     Update #: 79
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

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QTableView, QWidget, QLabel, QVBoxLayout)

from hdfattributemodel import HDFAttributeModel

class HDFAttributeWidget(QWidget):
    """Convenience widget to display HDF attributes.

    It creates a model when dataset is assigned. Like HDFDatasetWidget
    it assigns filename:nodename.attributes to its `name` field which
    is used by main window to set the window title of this subwindow.

    """
    def __init__(self, parent=None, node=None):
        super().__init__(parent)        
        self.name = ''
        self.nameLabel = QLabel('', self)
        self.nameLabel.setWordWrap(True)
        self.nameLabel.setTextInteractionFlags(Qt.TextSelectableByKeyboard | Qt.TextSelectableByMouse)
        self.fileLabel = QLabel('', self)
        self.fileLabel.setWordWrap(True)
        self.fileLabel.setTextInteractionFlags(Qt.TextSelectableByKeyboard | Qt.TextSelectableByMouse)
        self.attributeView = QTableView(self)
        self.setLayout(QVBoxLayout())
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

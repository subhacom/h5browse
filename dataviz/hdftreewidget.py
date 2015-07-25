# hdftreewidget.py --- 
# 
# Filename: hdftreewidget.py
# Description: 
# Author: subha
# Maintainer: 
# Created: Fri Jul 24 20:54:11 2015 (-0400)
# Version: 
# Last-Updated: Fri Jul 24 23:24:26 2015 (-0400)
#           By: subha
#     Update #: 60
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
"""

"""

from PyQt5.QtWidgets import QTreeView, QWidget

from hdfmodeltree import HDFTreeModel

class HDFTreeWidget(QWidget):
    """Convenience class to display HDF file trees. 

    HDFTreeWidget wraps an HDFTreeModel and a TreeView to display it.
    In addition it allows opening multiple files from a list.

    """
    def __init__(self, parent=None, flags=None):
        QWidget.__init__(self, parent, flags)
        self.model = HDFTreeModel([])
        self.view = QTreeView(self)
        self.view.setModel(self.model)
        layout = QVBoxLayout(self)
        layout.addWidget(view)

    def openFiles(self, files):
        """Function to open the files listed in argument.

        files: list of file paths. For example, output of
               QFileDialog::getOpenFileNames

        """
        for fname in files:
            self.model.openFile(fname)
        
    def closeFiles(self):
        """Close the files selected in the model."""
        indices = self.view.selectedIndexes()
        for index in indices:
            self.model.closeFile(index)


# 
# hdftreewidget.py ends here

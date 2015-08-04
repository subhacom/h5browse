# hdftreewidget.py --- 
# 
# Filename: hdftreewidget.py
# Description: 
# Author: subha
# Maintainer: 
# Created: Fri Jul 24 20:54:11 2015 (-0400)
# Version: 
# Last-Updated: Mon Aug  3 23:44:32 2015 (-0400)
#           By: subha
#     Update #: 175
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

from collections import defaultdict

from PyQt5.QtCore import (Qt, pyqtSignal)
from PyQt5.QtWidgets import (QTreeView, QWidget)

from hdftreemodel import HDFTreeModel
from hdfdatasetwidget import HDFDatasetWidget


class HDFTreeWidget(QTreeView):
    """Convenience class to display HDF file trees. 

    HDFTreeWidget wraps an HDFTreeModel and displays it.
    In addition it allows opening multiple files from a list.

    """
    datasetWidgetCreated = pyqtSignal(QWidget)

    def __init__(self, parent=None):
        super().__init__(parent)
        model = HDFTreeModel([])
        self.setModel(model)
        self.openDatasetViews = defaultdict(set)

    def openFiles(self, files):
        """Open the files listed in argument.

        files: list of file paths. For example, output of
               QFileDialog::getOpenFileNames

        """
        for fname in files:
            self.model().openFile(fname)
        
    def closeFiles(self):
        """Close the files selected in the model."""
        indices = self.view.selectedIndexes()
        for index in indices:
            item = self.model().getItem(index)            
            filename = item.h5node.file.filename
            if self.model().closeFile(index):
                for datasetView in self.openDatasetViews[filename]:
                    datasetView.close()
                    del(datasetView)
                self.openDatasetViews[filename].clear()

    def createDatasetWidget(self, index):
        """Returns a dataset widget for specified index.

        It assigns filename:datasetname as the object name for the
        widget. This may be useful for searching for items to be
        closed.

        """
        item = self.model().getItem(index)
        if (item is not None) and item.isDataset():
            # TODO maybe avoid duplicate windows for a dataset
            widget = HDFDatasetWidget(dataset=item.h5node)
            self.openDatasetViews[item.h5node.file.filename].add(widget)
            print('Sending', widget)
            self.datasetWidgetCreated.emit(widget)
            
        

if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import (QApplication, QMainWindow)
    app = QApplication(sys.argv)
    window = QMainWindow()
    widget = HDFTreeWidget()
    window.setCentralWidget(widget)
    widget.openFiles(['poolroom.h5'])
    window.show()
    sys.exit(app.exec_())

# 
# hdftreewidget.py ends here

# hdfdatasetwidget.py --- 
# 
# Filename: hdfdatasetwidget.py
# Description: 
# Author: subha
# Maintainer: 
# Created: Wed Jul 29 23:00:06 2015 (-0400)
# Version: 
# Last-Updated: Thu Jul 30 00:41:58 2015 (-0400)
#           By: subha
#     Update #: 58
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

from PyQt5.QtWidgets import (QTableView, QWidget, QVBoxLayout)

from hdfdatasetmodel import HDFDatasetModel, HDFDatasetNDModel, create_default_model

class HDFDatasetWidget(QWidget):
    """Convenience widget to display HDF datasets.

    It will create a model and view when the dataset is assigned.

    """
    def __init__(self, parent=None, flags=None, dataset=None):
        if flags == None:
            QWidget.__init__(self, parent)
        else:
            QWidget.__init__(self, parent, flags)        
        self.view = QTableView(self)
        layout = QVBoxLayout(self)
        layout.addWidget(self.view)
        if dataset is not None:
            self.model = create_default_model(dataset)
            self.view.setModel(self.model)
        else:
            self.model = None

    def setDataset(self, dataset):
        self.model = create_default_model(dataset)
        self.view.setModel(self.model)


if __name__ == '__main__':
    import sys
    import h5py as h5
    from PyQt5.QtWidgets import (QApplication, QMainWindow, QHBoxLayout, QWidget)
    app = QApplication(sys.argv)
    window = QMainWindow()
    fd = h5.File('poolroom.h5', 'r')
    widget1 = HDFDatasetWidget(dataset=fd['/map/nonuniform/tables/players'])
    widget2 = HDFDatasetWidget(dataset=fd['/data/uniform/ndim/data3d'])
    widget3 = HDFDatasetWidget()
    widget3.setDataset(fd['/data/uniform/balls/x'])
    widget = QWidget(window)
    layout = QHBoxLayout(widget)
    layout.addWidget(widget1)
    layout.addWidget(widget2)
    layout.addWidget(widget3)
    widget.setLayout(layout)
    window.setCentralWidget(widget)    
    window.show()
    sys.exit(app.exec_())

# 
# hdfdatasetwidget.py ends here
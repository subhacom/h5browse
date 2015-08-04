# hdfdatasetwidget.py --- 
# 
# Filename: hdfdatasetwidget.py
# Description: 
# Author: subha
# Maintainer: 
# Created: Wed Jul 29 23:00:06 2015 (-0400)
# Version: 
# Last-Updated: Tue Aug  4 00:22:39 2015 (-0400)
#           By: subha
#     Update #: 92
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
from PyQt5.QtWidgets import (QTableView, QWidget, QVBoxLayout)

from hdfdatasetmodel import HDFDatasetModel, HDFDatasetNDModel, create_default_model

class HDFDatasetWidget(QTableView):
    """Convenience widget to display HDF datasets.

    It will create a model when the dataset is assigned. Also, it
    assigns filename:datasetname to its `name` field which is used by
    main window to set the window title of this subwindow.

    """
    def __init__(self, parent=None, dataset=None):
        super().__init__(parent)        
        self.name = ''
        if dataset is not None:
            self.setDataset(dataset)

    def setDataset(self, dataset):
        model = create_default_model(dataset)
        self.setModel(model)
        self.name = dataset.name
        self.setToolTip('{}:{}'.format(dataset.file.filename,
                                       dataset.name))


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

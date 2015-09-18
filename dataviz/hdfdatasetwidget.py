# hdfdatasetwidget.py --- 
# 
# Filename: hdfdatasetwidget.py
# Description: 
# Author: subha
# Maintainer: 
# Created: Wed Jul 29 23:00:06 2015 (-0400)
# Version: 
# Last-Updated: Fri Sep 18 13:22:14 2015 (-0400)
#           By: Subhasis Ray
#     Update #: 112
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

from hdfdatasetmodel import (HDFDatasetModel, OneDDatasetModel,
                             TwoDDatasetModel, NDDatasetModel,
                             CompoundDatasetModel, ScalarDatasetModel,
                             create_default_model)

class HDFDatasetWidget(QtGui.QTableView):
    """Convenience widget to display HDF datasets.

    It will create a model when the dataset is assigned. Also, it
    assigns filename:datasetname to its `name` field which is used by
    main window to set the window title of this subwindow.

    """
    def __init__(self, parent=None, dataset=None):
        super(HDFDatasetWidget, self).__init__(parent)        
        self.name = ''
        if dataset is not None:
            self.setDataset(dataset)

    def setDataset(self, dataset):
        model = create_default_model(dataset)
        self.setModel(model)
        self.name = '{}:{}'.format(dataset.file.filename,
                                   dataset.name)
        self.setToolTip('Dataset <b>{}</b> [file: {}]'.format(
            dataset.name, dataset.file.filename))


if __name__ == '__main__':
    import sys
    import h5py as h5
    app = QtGui.QApplication(sys.argv)
    window = QtGui.QMainWindow()
    fd = h5.File('poolroom.h5', 'r')
    widget1 = HDFDatasetWidget(dataset=fd['/map/nonuniform/tables/players'])
    widget2 = HDFDatasetWidget(dataset=fd['/data/uniform/ndim/data3d'])
    widget3 = HDFDatasetWidget()
    widget3.setDataset(fd['/data/uniform/balls/x'])
    widget = QtGui.QWidget(window)
    layout = QtGui.QHBoxLayout(widget)
    layout.addWidget(widget1)
    layout.addWidget(widget2)
    layout.addWidget(widget3)
    widget.setLayout(layout)
    window.setCentralWidget(widget)    
    window.show()
    sys.exit(app.exec_())

# 
# hdfdatasetwidget.py ends here

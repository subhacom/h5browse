# datasetplot.py --- 
# 
# Filename: datasetplot.py
# Description: 
# Author: Subhasis Ray
# Maintainer: 
# Created: Fri Aug 21 17:21:21 2015 (-0400)
# Version: 
# Package-Requires: ()
# Last-Updated: Sat Aug 22 19:54:47 2015 (-0400)
#           By: subha
#     Update #: 268
# URL: 
# Doc URL: 
# Keywords: 
# Compatibility: 
# 
# 

# Commentary: 
# 
# 
# 

# Change Log:
# 
# 
# 
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or (at
# your option) any later version.
# 
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with GNU Emacs.  If not, see <http://www.gnu.org/licenses/>.
# 
# 

# Code:

from PyQt5.QtCore import Qt
import pyqtgraph as pg
from pyqtgraph import parametertree as ptree
import numpy as np
from hdfdatasetmodel import (HDFDatasetModel)




class DatasetPlotParamTree(ptree.ParameterTree):
    """Base class for ParameterTree to select plotting parameters specific
    to various dataset types.

    """
    def __init__(self, parent=None, showHeader=True, datasetModel=None):
        super().__init__(parent=parent,
                         showHeader=showHeader)        
        self.datasetModel = datasetModel

    def setDatasetModel(self, datasetModel):
        self.datasetModel = datasetModel


class OneDPlotParamTree(DatasetPlotParamTree):
    """1D datasets can only be plotted as x or y, with the other axis
    being the index."""
    def __init__(self, parent=None, showHeader=True, datasetModel=None):
        super().__init__(parent=parent,
                         showHeader=showHeader,
                         datasetModel=datasetModel)
        dataSources = ['index', 'data']
        self.xsource = ptree.Parameter.create(name='x-data',
                                           type='list',
                                           values=dataSources,
                                           value=dataSources[0])
        self.ysource = ptree.Parameter.create(name='y-data',
                                           type='list',
                                           values=dataSources,
                                           value=dataSources[1])
        self.dataSources = ptree.Parameter.create(name='Data sources',
                                               type='group',
                                               children=[self.xsource, self.ysource])
        self.addParameters(self.dataSources)            


        
class CompoundPlotParamTree(OneDPlotParamTree):
    """Compound dataset is tabulated data. One can choose row index or a
    (named)column for x and another column or row index as
    y. Generally it is unsafe to select rows because if different
    coumns have different data types (non numeric), this will
    crash. Also, for named columns, it does not make much sense unless
    the columns are categorical data.

    Keep scatter plot for the future.

    """
    def __init__(self, parent=None, showHeader=True, datasetModel=None):
        super().__init__(parent=parent,
                         showHeader=showHeader,
                         datasetModel=datasetModel)
        self.setDatasetModel(datasetModel)

    def setDatasetModel(self, datasetModel):
        if self.datasetModel is None:
            return
        self.datasetModel = datasetModel
        dataSources = ['index'] + \
                      [datasetModel.headerData(ii, Qt.Horizontal, Qt.DisplayRole) \
                       for ii in range(datasetModel.columnCount(datasetModel.createIndex(0,0)))]
        self.xsource.setLimits(dataSources)
        self.ysource.setLimits(dataSources)
        self.ysource.setValue(dataSources[1])
    

# class DatasetPlotParams(ptree.ParameterTree):
#     """Class to allow the user to choose parameters for plotting."""

#         params = {}
#         ndim = len(dataset.shape)
#         if ndim < 1:
#             return
#         if ndim == 1:
#             if dataset.dtype.names is not None:
#                 dataSources = dataset.dtype.names + ['index']
#             else:
#                 dataSources = ['row', 'index']
#             self.xchoice = ptree.Parameter.create(name='x-data', 
#                                                type='list',
#                                                values=dataSources,
#                                                value='index')
#             self.ychoice = ptrr.Parameter.create(name='y-data', 
#                                               type='list',
#                                               values=dataSources,
#                                               value=dataSources[0])
#             self.addParameters(self.xchoice)
#             self.addParameters(self.ychoice)
#             # TODO connect change in param to appropriate action
#         else:
#             # N-dim dataset. First choose which dimension to do select data from. Then 
#             self.dataDim = ptree.Parameter.create(name='Data dimension',
#                                                type='list',
#                                                values=range(ndim),
#                                                value=0)
#             dimChoices = [{'name': 'Dim {}'.format(ii),
#                            'type': 'list',
#                            'values': range(dataset.shape[ii]),
#                            'value': 0} for ii in range(ndim).pop(0)]
#             self.xchoice = ptree.Parameter.create(name='x-data',
#                                                type='group',
#                                                children=dimChoices)
#             self.ychoice = ptree.Parameter.create(name='y-data',
#                                                type='group',
#                                                children=dimChoices)
            
#             self.addParameters(self.xchoice)
#             self.addParameters(self.ychoice)
    
            
class DatasetPlot(pg.PlotWidget):
    """PlotWidget with some minor modifications for dataviz.
    
    """
    # TODO: multiple dataset in same plotwidget? cannot attach to a
    # specific dataset. Update `name` with something more meaningful. Also, allow option of plo
    def __init__(self, *args):
        pg.PlotWidget.__init__(self, *args)
        self.name = ''

    def plotTimeSeries(self, dataset):
        print(dataset, dataset.shape)
        time = np.arange(len(dataset))
        # try: # This is my data dump sepcific ...
        #     sched = dataset.file['/runconfig/scheduling']
        #     print('sched:', sched)
        #     time = np.arange(len(dataset)) * float(sched['simtime']) / len(dataset)
        # except KeyError:
        #     time = np.arange(len(dataset))
        self.plot(time, dataset)
        self.name = '{}:{}'.format(dataset.file.filename,
                                   dataset.name)


import h5py as h5
from hdfdatasetmodel import (CompoundDatasetModel, NDDatasetModel, TwoDDatasetModel, OneDDatasetModel, create_default_model)

if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import (QApplication, QMainWindow, QHBoxLayout, QTreeView, QWidget, QTableView)
    app = QApplication(sys.argv)
    fd = h5.File('poolroom.h5')
    twodModel = create_default_model(fd['/data/uniform/balls/x'])
    ndModel = create_default_model(fd['/data/uniform/ndim/data3d'], pos=('*', 1, '*'))
    widget = QWidget()
    widget.setLayout(QHBoxLayout())
    onedModel = create_default_model(fd['/data/event/balls/hit/ball_0_9ba91cb6163611e5899524fd526610e7'])    
    onedParams = OneDPlotParamTree(datasetModel=onedModel)
    widget.layout().addWidget(onedParams)
    compoundModel = create_default_model(fd['/data/static/tables/dimensions'])
    compoundParams = CompoundPlotParamTree(datasetModel=compoundModel)
    widget.layout().addWidget(compoundParams)
    widget.show()
    sys.exit(app.exec_())


# 
# datasetplot.py ends here

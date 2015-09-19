# datasetplot.py --- 
# 
# Filename: datasetplot.py
# Description: 
# Author: Subhasis Ray
# Maintainer: 
# Created: Fri Aug 21 17:21:21 2015 (-0400)
# Version: 
# Package-Requires: ()
# Last-Updated: Fri Sep 18 21:10:45 2015 (-0400)
#           By: subha
#     Update #: 834
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

import numpy as np
from collections import defaultdict
from pyqtgraph import QtCore
import pyqtgraph as pg
from pyqtgraph import parametertree as ptree
import numpy as np
from hdfdatasetmodel import datasetType

class DatasetPlotParamTree(ptree.ParameterTree):
    """Base class for ParameterTree to select plotting parameters specific
    to various dataset types.

    """
    sigUpdateData = QtCore.pyqtSignal() 
    
    def __init__(self, parent=None, showHeader=True, dataset=None):
        super(DatasetPlotParamTree, self).__init__(parent=parent,
                         showHeader=showHeader)        
        self.dataset = dataset
        self.updatePlotData = ptree.Parameter.create(name='updatePlotData',
                                                     title='Update plot data',
                                                     type='action')
        self.addParameters(self.updatePlotData)
        self.updatePlotData.sigActivated.connect(self.sigUpdateData)

    def setDataset(self, dataset):
        self.dataset = dataset


class OneDPlotParamTree(DatasetPlotParamTree):
    """1D datasets can only be plotted as x or y, with the other axis
    being the index."""
    def __init__(self, parent=None, showHeader=True, dataset=None):
        super(OneDPlotParamTree, self).__init__(parent=parent,
                         showHeader=showHeader,
                         dataset=dataset)
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

    def getXY(self):
        if self.xsource.value() == 'index':
            xdata = range(self.dataset.shape[0])
        else:
            xdata = self.dataset
        if self.ysource.value() == 'index':
            ydata  = range(self.dataset.shape[0])
        else:
            ydata = self.dataset
        return xdata, ydata
        
class CompoundPlotParamTree(OneDPlotParamTree):
    """Compound dataset is tabulated data. One can choose row index or a
    (named)column for x and another column or row index as
    y. Generally it is unsafe to select rows because if different
    coumns have different data types (non numeric), this will
    crash. Also, for named columns, it does not make much sense unless
    the columns are categorical data.

    Keep scatter plot for the future.

    """
    def __init__(self, parent=None, showHeader=True, dataset=None):
        super(CompoundPlotParamTree, self).__init__(parent=parent,
                         showHeader=showHeader,
                         dataset=dataset)
        self.setDataset(dataset)

    def setDataset(self, dataset):
        self.dataset = dataset
        dataSources = ['index'] + list(dataset.dtype.names)
        # print('compund data sources', dataSources)
        self.xsource.setLimits(dataSources)
        self.ysource.setLimits(dataSources)
        self.ysource.setValue(dataSources[1])

    def getXY(self):
        if self.xsource.value() == 'index':
            xdata = range(self.dataset.shape[0])
        else:
            xdata = self.dataset[self.xsource.value()]
        if self.ysource.value() == 'index':
            ydata = range(self.dataset.shape[0])
        else:
            ydata = self.dataset[self.ysource.value()]
        return xdata, ydata
    

class TwoDPlotParamTree(DatasetPlotParamTree):
    """For 2D dataset one can choose data from rows or from columns.
    """
    def __init__(self, parent=None, showHeader=True, dataset=None):
        super(TwoDPlotParamTree, self).__init__(parent=parent,
                         showHeader=showHeader,
                         dataset=dataset)
        self.dataDim = ptree.Parameter.create(name='datadim',
                                              title='Data in:',
                                              type='list',
                                              values=['rows', 'columns'],
                                              value='columns')
        dataSources = ['index', '0']
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
                                                  children=[self.dataDim,
                                                            self.xsource,
                                                            self.ysource])
        self.dataDim.sigValueChanged.connect(self.dataDimChanged)
        self.addParameters(self.dataSources)            
        self.setDatasetModel(dataset)

    def setDatasetModel(self, dataset):
        self.dataset = dataset
        if self.dataDim.value() == 'columns':
            dataSources = ['index'] + list(range(dataset.shape[1]))
        else:
            dataSources = ['index'] + list(range(dataset.shape[0]))
        self.xsource.setLimits(dataSources)
        self.xsource.setValue(dataSources[0])
        self.ysource.setLimits(dataSources)
        self.ysource.setValue(dataSources[1])

    def dataDimChanged(self):
        if self.dataDim.value() == 'columns':
            headerData = list(range(self.dataset.shape[1]))
        else:
            headerData = list(range(self.dataset.shape[0]))
        # print('TwoDPlotParamTree: dataset', self.dataset)
        dataSources = ['index'] + headerData
        # print('headerData', dataSources)
        self.xsource.setLimits(dataSources)
        self.xsource.setValue(dataSources[0])
        self.ysource.setLimits(dataSources)
        self.ysource.setValue(dataSources[1])

    def getXY(self):
        # print('2D', self, self.dataset)
        ds = self.dataset
        xdim = self.xsource.value()
        ydim = self.ysource.value()
        if self.dataDim.value() == 'rows':
            if xdim == 'index':
                xdata = range(ds.shape[1])
            else:
                xdata = ds[xdim,:]
            if ydim == 'index':
                ydata = range(ds.shape[1])
            else:
                ydata = ds[ydim, :]
        elif self.dataDim.value() == 'columns':
            if xdim == 'index':
                xdata = range(ds.shape[0])
            else:
                xdata = ds[:, xdim]
            if ydim == 'index':
                ydata = range(ds.shape[0])
            else:
                ydata = ds[:, ydim]        
        return xdata, ydata


class NDPlotParamTree(DatasetPlotParamTree):
    """Class to allow the user to choose parameters for plotting."""
    def __init__(self, parent=None, showHeader=True, dataset=None):
        super(NDPlotParamTree, self).__init__(parent=parent,
                         showHeader=showHeader,
                         dataset=dataset)
        self.dataDim = ptree.Parameter.create(name='datadim',
                                              title='Data along dimension:',
                                              type='list',
                                              values=[0],
                                              value=0)
        self.dataDim.sigValueChanged.connect(self.dataDimChanged)
        dataSources = ['index', '0']
        self.xsource = ptree.Parameter.create(name='x-data',
                                           type='group')
        self.ysource = ptree.Parameter.create(name='y-data',
                                           type='group')
        self.dataSources = ptree.Parameter.create(name='Data sources',
                                                  type='group',
                                                  children=[self.dataDim,
                                                            self.xsource,
                                                            self.ysource])
        self.addParameters(self.dataSources)            
        self.setDatasetModel(dataset)

    def setDatasetModel(self, dataset):
        self.dataset = dataset
        ndim = len(dataset.shape)
        self.dataDim.setLimits(range(len(dataset.shape)))
        dimChoices = [{'name': 'dim{}'.format(ii),
                       'title': str(ii),
                       'type': 'list',
                       'values': ['index']+list(range(dataset.shape[ii])),
                       'value': 0} for ii in range(1, ndim)]
        self.xsource.clearChildren()
        self.xsource.addChildren(dimChoices)
        self.ysource.clearChildren()
        self.ysource.addChildren(dimChoices)    

    def dataDimChanged(self):
        dims = list(range(len(self.dataset.shape)))
        dims.pop(self.dataDim.value())
        dimChoices = [{'name': 'dim{}'.format(ii),
                       'title': str(ii),
                       'type': 'list',
                       'values': ['index']+list(range(self.dataset.shape[ii])),
                       'value': 'index'} for ii in dims]
        self.xsource.clearChildren()
        self.xsource.addChildren(dimChoices)        
        for choice in dimChoices:
            choice['value'] = 0
        self.ysource.clearChildren()
        self.ysource.addChildren(dimChoices)

    def getXY(self):
        # print('NDPlotParamTree: xsource: {}, ysource: {}'.format(
        #     self.xsource.value(), self.ysource.value()))
        dims = range(len(self.dataset.shape))
        xindex = []
        yindex = []
        dataDim = self.dataDim.value()
        for dim in dims:
            if dim == dataDim:
                xindex.append(slice(self.dataset.shape[dim]))
                yindex.append(slice(self.dataset.shape[dim]))
                continue
            xparam = self.xsource.param('dim{}'.format(dim))
            xindex.append(xparam.value())
            yparam = self.ysource.param('dim{}'.format(dim))
            yindex.append(yparam.value())
        # data = np.asarray(self.dataset)
        if 'index' in  xindex:
            xdata = range(self.dataset.shape[dataDim])
        else:
            # This fancy indexing does not work with h5py dataset
            # xdata = self.dataset[xindex] 
            # Therefore using hack
            xdata = eval('self.dataset{}'.format(xindex))
            # xdata = data[xindex]
        if 'index' in  yindex:
            ydata = range(self.dataset.shape[dataDim])
        else:
            ydata = eval('self.dataset{}'.format(yindex))
            # ydata = data[yindex]
        return (xdata, ydata)
        
        
            
class DatasetPlot(pg.PlotWidget):
    """PlotWidget with some minor modifications for dataviz.
    
    """
    # TODO: multiple dataset in same plotwidget? cannot attach to a
    # specific dataset. Update `name` with something more meaningful. Also, allow option of plo
    def __init__(self, parent=None, background='default', **kwargs):
        super(DatasetPlot, self).__init__(parent=parent, background=background, **kwargs)
        self.name = ''        
        self.plotToParams = {}
        self.paramsToPlots = {}

    def plotLine(self, dataset):
        self.setToolTip(dataset.name)
        dtype = datasetType(dataset)
        if dtype == 'scalar':
            return
        if dtype == 'compound':
            params = CompoundPlotParamTree(dataset=dataset)
        elif dtype == '1d':
            params = OneDPlotParamTree(dataset=dataset)
        elif dtype == '2d':
            params = TwoDPlotParamTree(dataset=dataset)
        else: # dtype == 'nd':
            params = NDPlotParamTree(dataset=dataset)
        params.name = dataset.name
        params.sigUpdateData.connect(self.updatePlotData)
        #A better idea may be to keep all the params under a single tree
        # self.params[dataset].append(params)
        params.show()
        xdata, ydata = params.getXY()
        # try: # This is my data dump sepcific ... crashes in h5py on python3/cygwin?
        #     sched = dataset.file['/runconfig/scheduling']
        #     print('sched:', sched)
        #     xdata = np.arange(len(dataset)) * float(sched['simtime']) / len(dataset)
        # except KeyError:
        #     xdata = np.arange(len(dataset))
        plotDataItem = self.plot(xdata, ydata)
        self.plotToParams[plotDataItem] = params
        self.paramsToPlots[params] = plotDataItem
        # print('Plot=', plot)
        self.name = '{}:{}'.format(dataset.file.filename,
                                   dataset.name)
        return plotDataItem, params

    def updatePlotData(self):
        if self.sender() != 0:
            x, y = self.sender().getXY()
            plotDataItem = self.paramsToPlots[self.sender()]
            plotDataItem.setData(x, y)


import h5py as h5
from hdfdatasetmodel import (CompoundDatasetModel, NDDatasetModel, TwoDDatasetModel, OneDDatasetModel, create_default_model)
from pyqtgraph import QtGui
import sys

def testDatasetPlotParams(fd):
    widget = QtGui.QWidget()
    widget.setLayout(QtGui.QHBoxLayout())
    onedParams = OneDPlotParamTree(dataset=fd['/data/event/balls/hit/ball_0_9ba91cb6163611e5899524fd526610e7'])
    widget.layout().addWidget(onedParams)
    compoundParams = CompoundPlotParamTree(dataset=fd['/data/static/tables/dimensions'])
    widget.layout().addWidget(compoundParams)
    twodParams = TwoDPlotParamTree(dataset=fd['/data/uniform/balls/x'])
    widget.layout().addWidget(twodParams)
    ndParams = NDPlotParamTree(dataset=fd['/data/uniform/ndim/data3d'])
    widget.layout().addWidget(ndParams)
    widget.show()
    return widget


def testDatasetPlot(fd):
    widget = QtGui.QWidget()
    widget.setLayout(QtGui.QGridLayout())
    oneDimPlot = DatasetPlot()
    plot, params = oneDimPlot.plotLine(fd['/data/event/balls/hit/ball_0_9ba91cb6163611e5899524fd526610e7'])
    widget.layout().addWidget(params, 0, 0)
    widget.layout().addWidget(oneDimPlot, 1, 0)        
    compoundPlot = DatasetPlot()
    plot, params = compoundPlot.plotLine(fd['/data/static/tables/dimensions'])
    widget.layout().addWidget(params, 0, 1)
    widget.layout().addWidget(compoundPlot, 1, 1)        
    twoDimPlot = DatasetPlot()
    plot, params = twoDimPlot.plotLine(fd['/data/uniform/balls/x'])
    widget.layout().addWidget(params, 0, 2)
    widget.layout().addWidget(twoDimPlot, 1, 2)
    nDimPlot = DatasetPlot()
    plot, params = nDimPlot.plotLine(fd['/data/uniform/ndim/data3d'])
    widget.layout().addWidget(params, 0, 3)
    widget.layout().addWidget(nDimPlot, 1, 3)
    widget.show()
    return widget
    
if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    with h5.File('poolroom.h5', 'r') as fd:
        dparamw = testDatasetPlotParams(fd)
        dplotw = testDatasetPlot(fd)
        sys.exit(app.exec_())


# 
# datasetplot.py ends here

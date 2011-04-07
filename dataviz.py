#!/usr/bin/env python

# Filename: dataviz.py
# Description: 
# Author: Subhasis Ray
# Maintainer: 
# Copyright (C) 2010 Subhasis Ray, all rights reserved.
# Created: Wed Dec 15 10:16:41 2010 (+0530)
# Version: 
# Last-Updated: Thu Apr  7 18:05:32 2011 (+0530)
#           By: Subhasis Ray
#     Update #: 1379
# URL: 
# Keywords: 
# Compatibility: 
# 
# 

# Commentary: 
# 
# This is for visualizing neuronal activity in animation from a hdf5
# data file.
# 
# Decided to use matplotlib/mlab instead of mayavi for the sake of ease of coding.

# Change log:
# 
# 2010-12-15 10:17:49 (+0530) -- initial version
#
# 2010-12-17 11:30:12 (+0530) -- working matplotlib 2D animation with
# randomly generated numbers.
#
# 2010-12-21 11:53:32 (+0530) -- realized that a better way to
# organize data would be to create /data/spike /data/Vm and /data/Ca
# in the MOOSE model and the corresponding tables under those with
# same name as the cell it is recording from. Depending on table name
# suffix is as bad as filename extensions in Windows - one has to be
# consistent with the assumptions about table names between the
# simulation code and the data analysis code.  Hence forking this away
# into code for analyzing newer data.
#
# 2011-02-11 15:26:02 (+0530) -- scrapped matplotlib/mayavi approach
# and going for simple 2D rasters with option for selecting tables and
# scrolling (using Qt).
#
# 2011-03-03 23:46:42 (+0530) -- h5py browsing tree is functional.
#
# 2011-03-06 14:12:59 (+0530) -- This has now been split into
# multipple files in the dataviz directory. Also, all data
# visualization code is being shifted to cortical/dataviz directory as
# they are independent of the simulation.

# 2011-04-06 11:43:25 (+0530) scrapped the old code in this file and
# starting over with the component widgets - h5f tree and spikeplot.

# Code:

import sys
import numpy

from PyQt4 import QtCore, QtGui, Qt
from spikeplot import SpikePlotWidget
from hdftree import H5TreeWidget
from datalist import UniqueListModel, UniqueListView
            
class DataVizWidget(QtGui.QMainWindow):
    def __init__(self, *args):
        QtGui.QMainWindow.__init__(self, *args)
        self.mdiArea = QtGui.QMdiArea(self)
        self.leftDock = QtGui.QDockWidget(self)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.leftDock)
        self.rightDock = QtGui.QDockWidget(self)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.rightDock)
        self.h5tree = H5TreeWidget(self.leftDock)
        self.h5tree.setSelectionMode(self.h5tree.MultiSelection)
        self.leftDock.setWidget(self.h5tree)
        self.dataList = UniqueListView()
        self.dataList.setModel(UniqueListModel(QtCore.QStringList([])))
        self.rightDock.setWidget(self.dataList)
        self.setCentralWidget(self.mdiArea) # for testing only
        self.__setupActions()
        self.__setupMenuBar()

    def __setupActions(self):
        self.quitAction = QtGui.QAction('&Quit', self)
        self.quitAction.setShortcut(QtGui.QKeySequence(self.tr('Ctrl+Q')))
        self.connect(self.quitAction, QtCore.SIGNAL('triggered()'), QtGui.qApp.quit)

        self.openAction = QtGui.QAction('&Open', self)
        self.openAction.setShortcut(QtGui.QKeySequence(self.tr('Ctrl+O')))
        self.connect(self.openAction, QtCore.SIGNAL('triggered()'), self.__openFileDialog)

        self.cascadeAction = QtGui.QAction('&Cascade', self)
        self.connect(self.cascadeAction, QtCore.SIGNAL('triggered()'), self.mdiArea.cascadeSubWindows)
        self.tileAction = QtGui.QAction('&Tile', self)
        self.connect(self.tileAction, QtCore.SIGNAL('triggered()'), self.mdiArea.tileSubWindows)

        self.rasterPlotAction = QtGui.QAction('&Raster plot', self)
        self.connect(self.rasterPlotAction, QtCore.SIGNAL('triggered()'), self.__makeRasterPlot)

        self.clearRasterListAction = QtGui.QAction('&Clear raster plot list', self)
        self.connect(self.clearRasterListAction, QtCore.SIGNAL('triggered()'), self.dataList.model().clear)
        
        self.h5tree.setContextMenuPolicy(Qt.Qt.CustomContextMenu)
        self.connect(self.h5tree, QtCore.SIGNAL('customContextMenuRequested(const QPoint&)'), self.__setupDataSelectionMenu)

        self.selectByRegexAction = QtGui.QAction('Select by regular expression', self)
        self.connect(self.selectByRegexAction, QtCore.SIGNAL('triggered()'), self.__popupRegexTool)
        
    def __setupMenuBar(self):
        fileMenu = self.menuBar().addMenu('&File')
        fileMenu.addAction(self.openAction)
        fileMenu.addAction(self.quitAction)
        windowMenu = self.menuBar().addMenu('&Window')
        windowMenu.addAction(self.cascadeAction)
        windowMenu.addAction(self.tileAction)
        toolsMenu = self.menuBar().addMenu('&Tools')
        toolsMenu.addAction(self.rasterPlotAction)
        toolsMenu.addAction(self.clearRasterListAction)
        toolsMenu.addAction(self.selectByRegexAction)
        
    def __openFileDialog(self):
        file_names = QtGui.QFileDialog.getOpenFileNames()
        for name in file_names:
            print 'Opening:', name
            self.h5tree.addH5Handle(str(name))

    def __setupDataSelectionMenu(self, point):
        print 'Custom context menu ...'
        self.dataMenu = QtGui.QMenu(self.tr('Data Selection'), self.h5tree)
        self.selectForRasterAction = QtGui.QAction(self.tr('Select for raster plot'), self.h5tree)
        self.connect(self.selectForRasterAction, QtCore.SIGNAL('triggered()'), self.__selectForRaster)
        self.dataMenu.addAction(self.selectForRasterAction)
        self.dataMenu.popup(point)

    def __selectForRaster(self):
        print 'selectForRaster'
        items = self.h5tree.selectedItems()
        for item in items:
            if item.childCount() > 0: # not a leaf node                
                print 'Ignoring non-leaf node:', item.text(0), 'childCount:', item.childCount()
                for ii in range(item.childCount()):
                    print ii, item.child(ii).text(0)
                continue
            path = item.path()
            print 'Selected node', path, 'for plotting.'
            self.dataList.model().insertItem(path)
        
    def __makeRasterPlot(self):        
        table_paths = self.dataList.model().stringList()
        data_list = []
        for path in table_paths:
            data = self.h5tree.getData(path)
            data_list.append(numpy.array(data))
        plotWidget = SpikePlotWidget()
        mdiChild = self.mdiArea.addSubWindow(plotWidget)
        plotWidget.addPlotCurveList(table_paths, data_list)
        mdiChild.show()

    def __popupRegexTool(self):
        self.regexDialog = QtGui.QDialog(self)
        self.regexDialog.setWindowTitle('Select data by regex')
        regexlabel = QtGui.QLabel(self.regexDialog)
        regexlabel.setText('Regular expression:')
        self.regexLineEdit = QtGui.QLineEdit(self.regexDialog)        
        okButton = QtGui.QPushButton('OK', self.regexDialog)
        self.connect(okButton, QtCore.SIGNAL('clicked()'), self.__plotDataByRegex)
        cancelButton = QtGui.QPushButton('Cancel', self.regexDialog)
        self.connect(cancelButton, QtCore.SIGNAL('clicked()'), self.regexDialog.reject)
        layout = QtGui.QGridLayout()
        layout.addWidget(regexlabel, 0, 0, 1, 2)
        layout.addWidget(self.regexLineEdit, 0, 2, 1, 2)
        layout.addWidget(okButton, 1, 0, 1, 1)
        layout.addWidget(cancelButton, 1, 2, 1, 1)
        self.regexDialog.setLayout(layout)
        self.regexDialog.show()
        
    def __plotDataByRegex(self):
        pattern = str(self.regexLineEdit.text())
        data_dict = self.h5tree.getDataByRe(pattern)
        for key in data_dict.keys():
            print key
        
if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    QtGui.qApp = app
    mainwin = DataVizWidget()
    mainwin.show()
    app.exec_()
# 
# dataviz.py ends here

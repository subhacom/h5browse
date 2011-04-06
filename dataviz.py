#!/usr/bin/env python

# Filename: dataviz.py
# Description: 
# Author: Subhasis Ray
# Maintainer: 
# Copyright (C) 2010 Subhasis Ray, all rights reserved.
# Created: Wed Dec 15 10:16:41 2010 (+0530)
# Version: 
# Last-Updated: Wed Apr  6 17:50:50 2011 (+0530)
#           By: Subhasis Ray
#     Update #: 1251
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
        self.leftDock.setWidget(self.h5tree)
        self.dataList = UniqueListView()
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
        
    def __setupMenuBar(self):
        fileMenu = self.menuBar().addMenu('&File')
        fileMenu.addAction(self.openAction)
        fileMenu.addAction(self.quitAction)
        windowMenu = self.menuBar().addMenu('&Window')
        windowMenu.addAction(self.cascadeAction)
        windowMenu.addAction(self.tileAction)
        
    def __openFileDialog(self):
        file_names = QtGui.QFileDialog.getOpenFileNames()
        for name in file_names:
            print 'Opening:', name
            self.h5tree.addH5Handle(str(name))

    def __doRasterPlot(self):
        pass
        
if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    QtGui.qApp = app
    mainwin = DataVizWidget()
    mainwin.show()
    app.exec_()
# 
# dataviz.py ends here

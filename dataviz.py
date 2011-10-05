#!/usr/bin/env python

# Filename: dataviz.py
# Description: 
# Author: Subhasis Ray
# Maintainer: 
# Copyright (C) 2010 Subhasis Ray, all rights reserved.
# Created: Wed Dec 15 10:16:41 2010 (+0530)
# Version: 
# Last-Updated: Wed Oct  5 14:12:50 2011 (+0530)
#           By: Subhasis Ray
#     Update #: 1856
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
# multiple files in the dataviz directory. Also, all data
# visualization code is being shifted to cortical/dataviz directory as
# they are independent of the simulation.

# 2011-04-06 11:43:25 (+0530) scrapped the old code in this file and
# starting over with the component widgets - h5f tree and spikeplot.

# Code:

import os
import sys
import numpy

from PyQt4 import QtCore, QtGui, Qt
from plotwidget import PlotWidget
from hdftree import H5TreeWidget
from datalist import UniqueListModel, UniqueListView
from plotconfig import PlotConfig
            
class DataVizWidget(QtGui.QMainWindow):
    def __init__(self, *args):
        QtGui.QMainWindow.__init__(self, *args)
        self.mdi_data_map = {}
        self.data_dict = {}
        self.mdiArea = QtGui.QMdiArea(self)
        self.mdiArea.setViewMode(self.mdiArea.TabbedView)
        self.leftDock = QtGui.QDockWidget(self)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.leftDock)
        self.rightDock = QtGui.QDockWidget(self)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.rightDock)
        self.h5tree = H5TreeWidget(self.leftDock)
        self.h5tree.setSelectionMode(self.h5tree.ExtendedSelection)
        self.h5tree.setContextMenuPolicy(Qt.Qt.CustomContextMenu)
        self.leftDock.setWidget(self.h5tree)
        self.dataList = UniqueListView()
        self.dataList.setModel(UniqueListModel(QtCore.QStringList([])))
        self.dataList.setSelectionMode(self.dataList.ExtendedSelection)
        self.dataList.setContextMenuPolicy(Qt.Qt.CustomContextMenu)        
        self.rightDock.setWidget(self.dataList)
        self.setCentralWidget(self.mdiArea)
        self.windowMapper = QtCore.QSignalMapper(self)
        self.connect(self.windowMapper, QtCore.SIGNAL('mapped(QWidget*)'),
                     self.__setActiveSubWindow)
        self.connect(self.h5tree, QtCore.SIGNAL('itemDoubleClicked(QTreeWidgetItem *, int )'), self.__displayData)

        self.plotConfig = PlotConfig(self)
        self.plotConfig.setVisible(False)        
        self.__setupActions()
        self.__setupMenuBar()

    def __setupActions(self):
        self.editLegendTextAction = QtGui.QAction(self.tr('Edit legend text'), self)
        self.connect(self.editLegendTextAction, QtCore.SIGNAL('triggered(bool)'), self.__editLegendText)
        self.configurePlotAction = QtGui.QAction(self.tr('Configure selected plots'), self)
	self.connect(self.configurePlotAction, QtCore.SIGNAL('triggered(bool)'), self.__configurePlots)

        self.togglePlotVisibilityAction = QtGui.QAction(self.tr('Toggle selected plots'), self)
        self.connect(self.togglePlotVisibilityAction, QtCore.SIGNAL('triggered(bool)'), self.__togglePlotVisibility)

        self.quitAction = QtGui.QAction('&Quit', self)        
        self.quitAction.setShortcut(QtGui.QKeySequence(self.tr('Ctrl+Q')))
        self.connect(self.quitAction, QtCore.SIGNAL('triggered()'), QtGui.qApp.quit)

        self.openAction = QtGui.QAction('&Open', self)
        self.openAction.setShortcut(QtGui.QKeySequence(self.tr('Ctrl+O')))
        self.connect(self.openAction, QtCore.SIGNAL('triggered()'), self.__openFileDialog)

        self.savePlotAction = QtGui.QAction('&Save plot', self)
        self.connect(self.savePlotAction, QtCore.SIGNAL('triggered()'), self.__savePlot)

        self.saveScreenshotAction = QtGui.QAction('Save screenshot', self)
        self.connect(self.saveScreenshotAction, QtCore.SIGNAL('triggered()'), self.__saveScreenshot)

        self.plotAction = QtGui.QAction('&Plot', self)
        self.connect(self.plotAction, QtCore.SIGNAL('triggered()'), self.__makeLinePlot)
        self.rasterPlotAction = QtGui.QAction('&Raster plot', self)
        self.connect(self.rasterPlotAction, QtCore.SIGNAL('triggered()'), self.__makeRasterPlot)

        self.removeSelectedAction = QtGui.QAction('Remove selected items', self)
        self.connect(self.removeSelectedAction, QtCore.SIGNAL('triggered()'), self.dataList.removeSelected)

        self.clearPlotListAction = QtGui.QAction('&Clear data list', self)
        self.connect(self.clearPlotListAction, QtCore.SIGNAL('triggered()'), self.dataList.model().clear)

        self.selectForPlotAction = QtGui.QAction(self.tr('Select for plotting'), self.h5tree)
        self.connect(self.selectForPlotAction, QtCore.SIGNAL('triggered()'), self.__selectForPlot)

        self.editXLabelAction = QtGui.QAction(self.tr('Edit X axis label'), self)
        self.connect(self.editXLabelAction, QtCore.SIGNAL('triggered()'), self.__editXAxisLabel)

        self.editYLabelAction = QtGui.QAction(self.tr('Edit Y axis label'), self)
        self.connect(self.editYLabelAction, QtCore.SIGNAL('triggered()'), self.__editYAxisLabel)

        self.editPlotTitleAction = QtGui.QAction(self.tr('Edit plot title '), self)
        self.connect(self.editPlotTitleAction, QtCore.SIGNAL('triggered()'), self.__editPlotTitle)

        self.fitSelectedCurvesAction = QtGui.QAction(self.tr('Fit selected curves'), self)
        self.connect(self.fitSelectedCurvesAction, QtCore.SIGNAL('triggered()'), self.__fitSelectedPlots)

        self.selectByRegexAction = QtGui.QAction('Select by regular expression', self)
        self.connect(self.selectByRegexAction, QtCore.SIGNAL('triggered()'), self.__popupRegexTool)

        self.displayPropertiesAction = QtGui.QAction('Properties', self)
        self.connect(self.displayPropertiesAction, QtCore.SIGNAL('triggered()'), self.__displayH5NodeProperties)

        self.displayDataAction = QtGui.QAction('Display data', self)
        self.connect(self.displayDataAction, QtCore.SIGNAL('triggered()'), self.__displayCurrentlySelectedItemData)

        self.displayLegendAction = QtGui.QAction('Display legend', self)
        self.displayLegendAction.setChecked(True)
        self.displayLegendAction.setEnabled(False)
        self.connect(self.displayLegendAction, QtCore.SIGNAL('triggered(bool)'), self.__displayLegend)
        
        self.switchMdiViewAction = QtGui.QAction('Subwindow view', self)
        self.connect(self.switchMdiViewAction, QtCore.SIGNAL('triggered()'), self.__switchMdiView)
        self.cascadeAction = QtGui.QAction('&Cascade', self)
        self.connect(self.cascadeAction, QtCore.SIGNAL('triggered()'), self.mdiArea.cascadeSubWindows)
        self.cascadeAction.setVisible(False)
        self.tileAction = QtGui.QAction('&Tile', self)
        self.connect(self.tileAction, QtCore.SIGNAL('triggered()'), self.mdiArea.tileSubWindows)
        self.tileAction.setVisible(False)
        
    def __setupMenuBar(self):
        self.fileMenu = self.menuBar().addMenu('&File')
        self.fileMenu.addAction(self.openAction)
        self.fileMenu.addAction(self.savePlotAction)
        self.fileMenu.addAction(self.saveScreenshotAction)
        self.fileMenu.addAction(self.quitAction)
        self.windowMenu = self.menuBar().addMenu('&Window')
        self.connect(self.windowMenu, QtCore.SIGNAL('aboutToShow()'), self.__updateWindowMenu)
        self.closeAction = QtGui.QAction('Close Current Window', self)
        self.connect(self.closeAction, QtCore.SIGNAL('triggered()'), self.mdiArea.closeActiveSubWindow)
        self.closeAllAction = QtGui.QAction('Close All Windows', self)
        self.connect(self.closeAllAction, QtCore.SIGNAL('triggered()'), self.mdiArea.closeAllSubWindows)
        self.editMenu = self.menuBar().addMenu('&Edit')
        self.editMenu.addAction(self.selectForPlotAction)
        self.editMenu.addAction(self.selectByRegexAction)
        self.editMenu.addAction(self.clearPlotListAction)

        self.plotMenu = self.menuBar().addMenu('&Plot')
        self.plotMenu.addAction(self.editLegendTextAction)
        self.plotMenu.addAction(self.configurePlotAction)
        self.plotMenu.addAction(self.togglePlotVisibilityAction)
        self.plotMenu.addAction(self.editXLabelAction)
        self.plotMenu.addAction(self.editYLabelAction)
        self.plotMenu.addAction(self.editPlotTitleAction)
        self.plotMenu.addAction(self.displayLegendAction)
        self.plotMenu.addAction(self.fitSelectedCurvesAction)
        
        self.toolsMenu = self.menuBar().addMenu('&Tools')
        self.toolsMenu.addAction(self.plotAction)
        self.toolsMenu.addAction(self.rasterPlotAction)
        # These are custom context menus
        self.h5treeMenu = QtGui.QMenu(self.tr('Data Selection'), self.h5tree)
        self.h5treeMenu.addAction(self.selectForPlotAction)
        self.h5treeMenu.addAction(self.selectByRegexAction)
        self.h5treeMenu.addAction(self.displayPropertiesAction)
        self.h5treeMenu.addAction(self.displayDataAction)
        self.connect(self.h5tree, QtCore.SIGNAL('customContextMenuRequested(const QPoint&)'), self.__popupH5TreeMenu)
        
        self.dataListMenu = QtGui.QMenu(self.tr('Selected Data'), self.dataList)
        self.dataListMenu.addAction(self.removeSelectedAction)
        self.dataListMenu.addAction(self.clearPlotListAction)
        self.connect(self.dataList, QtCore.SIGNAL('customContextMenuRequested(const QPoint&)'), self.__popupDataListMenu)
        
    def __openFileDialog(self):
        settings = QtCore.QSettings()
        last_dir = settings.value('lastVisitedDir').toString()
        file_names = QtGui.QFileDialog.getOpenFileNames(self, self.tr('Open hdf5 file'), last_dir)
        name = last_dir
        for name in file_names:
            self.h5tree.addH5Handle(str(name))
        settings.setValue('lastVisitedDir', QtCore.QString(os.path.dirname(str(name))))


    def __selectForPlot(self):
        items = self.h5tree.selectedItems()
        self.data_dict = {}
        for item in items:
            if item.childCount() > 0: # not a leaf node                
                print 'Ignoring non-leaf node:', item.text(0), 'childCount:', item.childCount()
                continue
            path = item.path()
            self.dataList.model().insertItem(path)
        
    def __makeRasterPlot(self):
        plotWidget = PlotWidget()
        self.displayLegendAction.setEnabled(True)
        mdiChild = self.mdiArea.addSubWindow(plotWidget)
        mdiChild.setWindowTitle('Plot %d' % len(self.mdiArea.subWindowList()))
        namelist = []
        datalist = []
        for item in self.dataList.model().stringList():
            path = str(item)
            tseries = self.h5tree.getTimeSeries(path)
            datalist.append((tseries, numpy.array(self.h5tree.getData(path))))
            namelist.append(path)
        plotWidget.addPlotCurveList(namelist, datalist, mode='raster')
        mdiChild.showMaximized()

    def __makeLinePlot(self):
        plotWidget = PlotWidget()
        mdiChild = self.mdiArea.addSubWindow(plotWidget)
        self.displayLegendAction.setEnabled(True)
        mdiChild.setWindowTitle('Plot %d' % len(self.mdiArea.subWindowList()))
        datalist = []
        pathlist = []
        for item in self.dataList.model().stringList():
            path = str(item)
            pathlist.append(path)
            filename = self.h5tree.getOpenFileName(path)
            simtime = self.h5tree.getAttribute(filename, 'simtime')
            data = numpy.array(self.h5tree.getData(path))
	    if simtime is None:
		simtime = 1.0 * len(data)
            tseries = numpy.linspace(0, simtime, len(data))
            datalist.append((tseries, data))
        plotWidget.addPlotCurveList(pathlist, datalist, mode='curve')
        mdiChild.showMaximized()

    def __editXAxisLabel(self):
        activePlot = self.mdiArea.activeSubWindow().widget()
        xlabel, ok, = QtGui.QInputDialog.getText(self, self.tr('Change X Axis Label'), self.tr('X axis label:'), QtGui.QLineEdit.Normal, activePlot.axisTitle(activePlot.xBottom).text())
        print xlabel
        if ok:
            print 'setting xlabel', xlabel
            activePlot.setAxisTitle(2, xlabel)
        
    def __editYAxisLabel(self):
        activePlot = self.mdiArea.activeSubWindow().widget()
        ylabel, ok, = QtGui.QInputDialog.getText(self, self.tr('Change Y Axis Label'), self.tr('Y axis label:'), QtGui.QLineEdit.Normal, activePlot.axisTitle(0).text())
        if ok:
            activePlot.setAxisTitle(0, ylabel)

    def __popupRegexTool(self):
        self.regexDialog = QtGui.QDialog(self)
        self.regexDialog.setWindowTitle('Select data by regex')
        regexlabel = QtGui.QLabel(self.regexDialog)
        regexlabel.setText('Regular expression:')
        self.regexLineEdit = QtGui.QLineEdit(self.regexDialog)        
        okButton = QtGui.QPushButton('OK', self.regexDialog)
        self.connect(okButton, QtCore.SIGNAL('clicked()'), self.regexDialog.accept)
        cancelButton = QtGui.QPushButton('Cancel', self.regexDialog)
        self.connect(cancelButton, QtCore.SIGNAL('clicked()'), self.regexDialog.reject)
        layout = QtGui.QGridLayout()
        layout.addWidget(regexlabel, 0, 0, 1, 2)
        layout.addWidget(self.regexLineEdit, 0, 2, 1, 2)
        layout.addWidget(okButton, 1, 0, 1, 1)
        layout.addWidget(cancelButton, 1, 2, 1, 1)
        self.regexDialog.setLayout(layout)
        if self.regexDialog.exec_() == QtGui.QDialog.Accepted:
            self.__selectDataByRegex(str(self.regexLineEdit.text()))
        
    def __selectDataByRegex(self, pattern):
        self.data_dict = self.h5tree.getDataByRe(pattern)
        self.dataList.model().clear()
        for key in self.data_dict.keys():
            self.dataList.model().insertItem(key)

    def __displayH5NodeProperties(self):
        attributes = self.h5tree.currentItem().getAttributes()
        displayWidget = QtGui.QTableWidget(self)
        displayWidget.setRowCount(len(attributes))
        displayWidget.setColumnCount(2)
        displayWidget.setHorizontalHeaderLabels(QtCore.QStringList(['Attribute', 'Value']))
        row = 0
        for key, value in attributes.items():
            newItem = QtGui.QTableWidgetItem(self.tr(str(key)))
            displayWidget.setItem(row, 0, newItem)
            newItem = QtGui.QTableWidgetItem(self.tr(str(value)))
            displayWidget.setItem(row, 1, newItem)
            row += 1
        mdiChild = self.mdiArea.addSubWindow(displayWidget)
        mdiChild.setWindowTitle(str(self.h5tree.currentItem().h5node.name))
        mdiChild.showMaximized()

    def __displayData(self, node, column):
        data = node.getHDF5Data()
        if data is None:
            return
        tableWidget = QtGui.QTableWidget()
        tableWidget.setRowCount(len(data))
        tableWidget.horizontalHeader().hide()
        if data.dtype.type == numpy.void:            
            tableWidget.setColumnCount(len(data.dtype.names))
            for row in range(len(data)):
                for column in range(len(data.dtype.names)):
                    item = QtGui.QTableWidgetItem(self.tr(str(data[row][column])))
                    tableWidget.setItem(row, column, item)
        else:
            tableWidget.setColumnCount(1)
            for row in range(len(data)):
                item = QtGui.QTableWidgetItem(self.tr(str(data[row])))
                tableWidget.setItem(row, 0, item)
        mdiChild = self.mdiArea.addSubWindow(tableWidget)
        mdiChild.showMaximized()
        mdiChild.setWindowTitle(str(node.h5node.name))
            
    def __displayCurrentlySelectedItemData(self):
        node = self.h5tree.currentItem().h5node
        self.__displayData(node, 0)


    def __switchMdiView(self):
        if self.mdiArea.viewMode() == self.mdiArea.TabbedView:
            self.mdiArea.setViewMode(self.mdiArea.SubWindowView)
        else:
            self.mdiArea.setViewMode(self.mdiArea.TabbedView)

    def __displayLegend(self, checked):
        activePlot = self.mdiArea.activeSubWindow().widget()
        if checked:
            activePlot.legend().show()
        else:
            activePlot.legend().hide()

    def __popupH5TreeMenu(self, point):
        if self.h5tree.model().rowCount() == 0:
            return
        globalPos = self.h5tree.mapToGlobal(point)
        self.h5treeMenu.exec_(globalPos)

    def __popupDataListMenu(self, point):
        if self.dataList.model().rowCount() == 0:
            return
        globalPos = self.dataList.mapToGlobal(point)
        self.dataListMenu.exec_(globalPos)

    def __updateWindowMenu(self):
        self.windowMenu.clear()
        if  len(self.mdiArea.subWindowList()) == 0:
            return
        self.windowMenu.addAction(self.closeAction)
        self.windowMenu.addAction(self.closeAllAction)
        self.windowMenu.addSeparator()
        self.windowMenu.addAction(self.switchMdiViewAction)
        if self.mdiArea.viewMode() == self.mdiArea.TabbedView:
            self.switchMdiViewAction.setText('Subwindow view')
        else:
            self.switchMdiViewAction.setText('Tabbed view')            
            self.windowMenu.addAction(self.cascadeAction)
            self.windowMenu.addAction(self.tileAction)
        self.windowMenu.addSeparator()
        activeSubWindow = self.mdiArea.activeSubWindow()
        for window in self.mdiArea.subWindowList():
            action = self.windowMenu.addAction(window.windowTitle())
            action.setCheckable(True)
            action.setChecked(window == activeSubWindow)
            self.connect(action, QtCore.SIGNAL('triggered()'), self.windowMapper, QtCore.SLOT('map()'))
            self.windowMapper.setMapping(action, window)

    def __setActiveSubWindow(self, window):
        if window:
            self.mdiArea.setActiveSubWindow(window)
            if isinstance(window.widget(), PlotWidget):
                self.displayLegendAction.setEnabled(True)
                self.displayLegendAction.setChecked(window.widget().legend().isVisible())
            else:
                self.displayLegendAction.setEnabled(False)
                

    def __editLegendText(self):
        """Change the legend text."""
        activePlot = self.mdiArea.activeSubWindow().widget()
        activePlot.editLegendText()

    def __editPlotTitle(self):
        activePlot = self.mdiArea.activeSubWindow().widget()
        title, ok, = QtGui.QInputDialog.getText(self, self.tr('Change Plot Title'), self.tr('Plot title:'), QtGui.QLineEdit.Normal, activePlot.title().text())
        if ok:
            activePlot.setTitle(title)
        

    def __configurePlots(self):
        """Interactively allow the user to configure everything about
        the plots."""
        activePlot = self.mdiArea.activeSubWindow().widget()
        self.plotConfig.setVisible(True)
        ret = self.plotConfig.exec_()
        # print ret, QtGui.QDialog.Accepted
        if ret == QtGui.QDialog.Accepted:
            pen = self.plotConfig.getPen()
            symbol = self.plotConfig.getSymbol()
            style = self.plotConfig.getStyle()
            attribute = self.plotConfig.getAttribute()
            print 'Active plot', activePlot
            activePlot.reconfigureSelectedCurves(pen, symbol, style, attribute)

    def __togglePlotVisibility(self, hide):
        print 'Currently selected to hide?', hide
        activePlot = self.mdiArea.activeSubWindow().widget()
        activePlot.toggleSelectedCurves()

    def __savePlot(self):
        activePlot = self.mdiArea.activeSubWindow().widget()
        if isinstance(activePlot, PlotWidget):
            filename = QtGui.QFileDialog.getSaveFileName(self,
                                                     'Save plot as',
                                                     '%s.png' % (str(self.mdiArea.activeSubWindow().windowTitle())),
                                                     'Images (*.png *.jpg *.gif);; All files (*.*)')
            activePlot.savePlotImage(filename)


    def __saveScreenshot(self):
        activeSubWindow = self.mdiArea.activeSubWindow()
        if activeSubWindow is None:
            print 'Active subwindow is empty!'
            return
        activePlot = activeSubWindow.widget()
        pixmap = QtGui.QPixmap.grabWidget(activePlot)
        filename = QtGui.QFileDialog.getSaveFileName(self,
                                                     'Save plot as',
                                                     '%s.png' % (str(self.mdiArea.activeSubWindow().windowTitle())),
                                                     'Images (*.png *.jpg *.gif);; All files (*.*)')
        pixmap.save(filename)


    def __fitSelectedPlots(self):
        """Do curve fitting on the selected plots."""
        activePlot = self.mdiArea.activeSubWindow().widget()
        activePlot.fitSelectedCurves()
        
if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    QtGui.qApp = app
    mainwin = DataVizWidget()
    mainwin.show()
    app.exec_()
# 
# dataviz.py ends here

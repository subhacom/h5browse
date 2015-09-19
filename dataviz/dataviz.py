#!/usr/bin/python3

# dataviz.py --- 
# 
# Filename: dataviz.py
# Description: 
# Author: subha
# Maintainer: 
# Created: Wed Jul 29 22:55:26 2015 (-0400)
# Version: 
# Last-Updated: Fri Sep 18 21:21:13 2015 (-0400)
#           By: subha
#     Update #: 486
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

import os
from pyqtgraph import QtCore
from pyqtgraph import QtGui
from hdftreewidget import HDFTreeWidget
from hdfdatasetwidget import HDFDatasetWidget
from datasetplot import (DatasetPlot, DatasetPlotParamTree)
from pyqtgraph import FileDialog


class DataViz(QtGui.QMainWindow):
    """The main application window for dataviz.

    This is an MDI application with dock displaying open HDF5 files on
    the left. Attributes of the selected item at left bottom.

    Signals
    -------

    sigOpen: Emitted when a set of files have been selected in the open
          files dialog. Sends out the list of file paths selected and the 
          mode string.
    
    sigCloseFiles: Emitted when the user triggers closeFilesAction. This
                is passed on to the HDFTreeWidget which decides which
                files to close based on selection.

    sigShowAttributes: Emitted when showAttributesAction is
                    triggered. Connected to
                    HDFTreeWidget.showAttributes function which
                    creates a widget for displaying attributes of the
                    HDF5 node of its current
                    item. HDFTreeWidget.showAttributes sends a return
                    signal `attributeWidgetCreated` with the created
                    widget so that the DataViz widget can incorporate
                    it as an mdi child window.

    sigShowDataset: Emitted when showDatasetAction is
                 triggered. Connected to HDFTreeWidget's showDataset
                 function which creates a widget for displaying the
                 contents of the HDF5 node if it is a dataset.
                 HDFTreeWidget.showDataset sends a return signal
                 `sigDatasetWidgetCreated` with the created widget so
                 that the DataViz widget can incorporate it as an mdi
                 child window.

    sigPlotDataset: Emitted when plotDatasetAction is
                  triggered. Connected to HDFTreeWidget's plotDataset
                  function which creates a widget for displaying teh
                  contents of the HDF5 node if it is a datset.

    """
    sigOpen = QtCore.pyqtSignal(list, str)
    sigCloseFiles = QtCore.pyqtSignal()
    sigShowAttributes = QtCore.pyqtSignal()
    sigShowDataset = QtCore.pyqtSignal()
    sigPlotDataset = QtCore.pyqtSignal()

    def __init__(self, parent=None, flags=QtCore.Qt.WindowFlags(0)):
        super(DataViz, self).__init__(parent=parent, flags=flags)
        self.readSettings()
        self.mdiArea = QtGui.QMdiArea()
        self.mdiArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.mdiArea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.mdiArea.subWindowActivated.connect(self.switchPlotParamPanel)
        self.setCentralWidget(self.mdiArea)
        self.createTreeDock()
        self.createActions()
        self.createMenus()

    def closeEvent(self, event):
        self.writeSettings()
        event.accept()

    def readSettings(self):
        settings = QtCore.QSettings('dataviz', 'dataviz')
        self.lastDir = settings.value('lastDir', '.', str)
        pos = settings.value('pos', QtCore.QPoint(200, 200))
        if isinstance(pos, QtCore.QVariant):
            pos = pos.toPyObject()
        self.move(pos)
        size = settings.value('size', QtCore.QSize(400, 400))
        if isinstance(size, QtCore.QVariant):
            size = size.toPyObject()
        self.resize(size)

    def writeSettings(self):
        settings = QtCore.QSettings('dataviz', 'dataviz')
        settings.setValue('lastDir', self.lastDir)
        settings.setValue('pos', self.pos())
        settings.setValue('size', self.size())

    def openFilesReadOnly(self, filePaths=None):
        if filePaths is None or filePaths is False:
            self.fileDialog = FileDialog(None, 'Open file(s) read-only', self.lastDir, 
                                                 'HDF5 file (*.h5 *.hdf);;All files (*)')
            self.fileDialog.show()
            self.fileDialog.filesSelected.connect(self.openFilesReadOnly)
            return
        # filePaths = QtGui.QFileDialog.getOpenFileNames(self, 
        #                                          'Open file(s)', self.lastDir,
        #                                          'HDF5 file (*.h5 *.hdf);;All files (*)')
        filePaths = [str(path) for path in filePaths]   # python2/qt4 compatibility
        if len(filePaths) == 0:
            return
        self.lastDir = QtCore.QFileInfo(filePaths[-1]).dir().absolutePath()
        # TODO handle recent files
        self.sigOpen.emit(filePaths, 'r')

    def openFilesReadWrite(self, filePaths=None):
        # print(filePaths)
        if filePaths is None or filePaths is False:
            self.fileDialog = FileDialog(None, 'Open file(s) read/write', self.lastDir, 
                                                 'HDF5 file (*.h5 *.hdf);;All files (*)')
            self.fileDialog.filesSelected.connect(self.openFilesReadWrite)
            self.fileDialog.show()
            return
        # filePaths = QtGui.QFileDialog.getOpenFileNames(self, 
        #                                          'Open file(s)', self.lastDir,
        #                                          'HDF5 file (*.h5 *.hdf);;All files (*)')
        filePaths = [str(path) for path in filePaths]        # python2/qt4 compatibility
        if len(filePaths) == 0:
            return
        self.lastDir = QtCore.QFileInfo(filePaths[-1]).dir().absolutePath()
        # TODO handle recent files
        self.sigOpen.emit(filePaths, 'r+')

    def openFileOverwrite(self, filePath=None, startDir=None):
        if filePath is None or filePaths is False:
            self.fileDialog = FileDialog(None, 'Open file(s) read/write', self.lastDir, 
                                                 'HDF5 file (*.h5 *.hdf);;All files (*)')
            self.fileDialog.show()
            self.fileDialog.fileSelected.connect(self.openFileOverwrite)
            return
        # filePath = QtGui.QFileDialog.getOpenFileName(self, 
        #                                          'Overwrite file', self.lastDir,
        #                                          'HDF5 file (*.h5 *.hdf);;All files (*)')
        if len(filePath) == 0:
            return
        self.lastDir = QtCore.QFileInfo(filePath).dir().absolutePath()
        # TODO handle recent files
        self.sigOpen.emit([filePath], 'w')

    def createFile(self, filePath=None, startDir=None):
        if filePath is None or filePaths is False:
            self.fileDialog = FileDialog(None, 'Open file(s) read/write', self.lastDir, 
                                                 'HDF5 file (*.h5 *.hdf);;All files (*)')
            self.fileDialog.show()
            self.fileDialog.fileSelected.connect(self.createFile)
            return
        # filePath = QtGui.QFileDialog.getOpenFileName(self, 
        #                                           'Overwrite file', self.lastDir,
        #                                           'HDF5 file (*.h5 *.hdf);;All files (*)')
        if len(filePath) == 0:
            return
        # print('%%%%%', filePath, _)
        self.lastDir = filePath.rpartition('/')[0]
        # TODO handle recent files
        self.sigOpen.emit([filePath], 'w-')
        
    def createActions(self):
        self.openFileReadOnlyAction = QtGui.QAction(QtGui.QIcon(), 'Open file(s) readonly', self,
                                   # shortcut=QtGui.QKeySequence.Open,
                                   statusTip='Open an HDF5 file for reading',
                                      triggered=self.openFilesReadOnly)
        self.openFileReadWriteAction = QtGui.QAction(QtGui.QIcon(), '&Open file(s) read/write', self,
                                   shortcut=QtGui.QKeySequence.Open,
                                   statusTip='Open an HDF5 file for editing',
                                               triggered=self.openFilesReadWrite)
        self.openFileOverwriteAction = QtGui.QAction(QtGui.QIcon(), 'Overwrite file', self,
                                               # shortcut=QtGui.QKeySequence.Open,
                                               statusTip='Open an HDF5 file for writing (overwrite existing)',
                                               triggered=self.openFileOverwrite)
        self.createFileAction = QtGui.QAction(QtGui.QIcon(), '&New file', self,
                                               shortcut=QtGui.QKeySequence.New,
                                               statusTip='Create a new HDF5 file',
                                               triggered=self.createFile)
        self.closeFileAction = QtGui.QAction(QtGui.QIcon(), '&Close file(s)',
                                       self,
                                       shortcut=QtGui.QKeySequence(QtCore.Qt.CTRL+QtCore.Qt.Key_K),
                                       statusTip='Close selected files',
                                       triggered=self.sigCloseFiles)
        self.quitAction = QtGui.QAction(QtGui.QIcon(), '&Quit', self,
                                  shortcut=QtGui.QKeySequence.Quit, 
                                  statusTip='Quit dataviz', 
                                  triggered=self.doQuit)
        self.showAttributesAction = QtGui.QAction(QtGui.QIcon(), 'Show attributes', self,
                                            shortcut=QtGui.QKeySequence.InsertParagraphSeparator,
                                            statusTip='Show attributes',
                                            triggered=self.sigShowAttributes)
        self.showDatasetAction = QtGui.QAction(QtGui.QIcon(), 'Show dataset', self,
                                            shortcut=QtGui.QKeySequence(QtCore.Qt.CTRL+QtCore.Qt.Key_Return),
                                            statusTip='Show dataset',
                                            triggered=self.sigShowDataset)
        self.plotDatasetAction = QtGui.QAction(QtGui.QIcon(), 'Plot dataset', self,
                                         shortcut=QtGui.QKeySequence(QtCore.Qt.ALT + QtCore.Qt.Key_P),
                                         statusTip='Plot dataset',
                                         triggered=self.sigPlotDataset)
        


    def createMenus(self):
        self.menuBar().setVisible(True)
        self.fileMenu = self.menuBar().addMenu('&File')
        self.fileMenu.addAction(self.openFileReadWriteAction)
        self.fileMenu.addAction(self.openFileReadOnlyAction)
        self.fileMenu.addAction(self.openFileOverwriteAction)
        self.fileMenu.addAction(self.createFileAction)
        self.fileMenu.addAction(self.closeFileAction)
        self.fileMenu.addAction(self.quitAction)
        self.editMenu = self.menuBar().addMenu('&Edit')
        self.editMenu.addAction(self.tree.insertDatasetAction)
        self.editMenu.addAction(self.tree.insertGroupAction)
        self.editMenu.addAction(self.tree.deleteNodeAction)
        self.viewMenu = self.menuBar().addMenu('&View')        
        self.viewMenu.addAction(self.treeDock.toggleViewAction())
        self.dataMenu = self.menuBar().addMenu('&Data')
        self.dataMenu.addAction(self.showAttributesAction)
        self.dataMenu.addAction(self.showDatasetAction)
        self.dataMenu.addAction(self.plotDatasetAction)

    def createTreeDock(self):
        self.treeDock = QtGui.QDockWidget('File tree', self)
        self.tree = HDFTreeWidget(parent=self.treeDock)
        self.sigOpen.connect(self.tree.openFiles)
        self.tree.doubleClicked.connect(self.tree.createDatasetWidget)
        self.tree.sigDatasetWidgetCreated.connect(self.addMdiChildWindow)
        self.tree.sigDatasetWidgetClosed.connect(self.closeMdiChildWindow)
        self.tree.sigAttributeWidgetCreated.connect(self.addMdiChildWindow)
        self.tree.sigAttributeWidgetClosed.connect(self.closeMdiChildWindow)
        self.tree.sigPlotWidgetCreated.connect(self.addMdiChildWindow)
        self.tree.sigPlotWidgetClosed.connect(self.closeMdiChildWindow)
        self.tree.sigPlotParamTreeCreated.connect(self.addPanelBelow)
        # pipe signals of dataviz to those of hdftree widget
        self.sigShowAttributes.connect(self.tree.showAttributes)
        self.sigShowDataset.connect(self.tree.showDataset)
        self.sigPlotDataset.connect(self.tree.plotDataset)
        self.sigCloseFiles.connect(self.tree.closeFiles)
        self.treeDock.setWidget(self.tree)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.treeDock)

    def addMdiChildWindow(self, widget):
        if widget is not None:
            subwin = self.mdiArea.addSubWindow(widget)
            subwin.setWindowTitle(widget.name)
            widget.show()
        return subwin

    def closeMdiChildWindow(self, widget):
        if widget is not None:
            for window in self.mdiArea.subWindowList():
                if window.widget() == widget:
                    window.deleteLater()

    def addPanelBelow(self, widget):
        dockWidget = QtGui.QDockWidget(widget.name)
        dockWidget.setWidget(widget)
        self.addDockWidget(QtCore.Qt.BottomDockWidgetArea, dockWidget)
        dockWidget.show()

    
    def switchPlotParamPanel(self, subwin):
        """Make plot param tree panel visible if active subwindow has a
        plotwidget. All other plot param trees will be invisible. Qt
        does not provide out-of-focus signal for mdi subwindows. So
        there is no counterpart of subWindowActivated that can allow
        us to hide paramtrees for inactive plot widgets. Hence this
        approach.

        """
        if subwin is None:
            return
        for dockWidget in self.findChildren(QtGui.QDockWidget):
            # All dockwidgets that contain paramtrees must be checked
            if isinstance(dockWidget.widget(), DatasetPlotParamTree):
                if isinstance(subwin.widget(), DatasetPlot) and \
                   dockWidget.widget() in subwin.widget().paramsToPlots:
                    dockWidget.setVisible(True)
                else:
                    dockWidget.setVisible(False)
        
    def doQuit(self):
        self.writeSettings()
        QtGui.QApplication.instance().closeAllWindows()
        

def main():
    import sys
    app = QtGui.QApplication(sys.argv)
    window = DataViz()
    window.show()
    app.exec_()
    # fixed segfaults at exit:
    # http://python.6.x6.nabble.com/Application-crash-on-exit-under-Linux-td5067510.html
    del window
    del app   
    sys.exit(0)

if __name__ == '__main__':
    main()

# 
# dataviz.py ends here

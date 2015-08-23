#!/usr/bin/python3

# dataviz.py --- 
# 
# Filename: dataviz.py
# Description: 
# Author: subha
# Maintainer: 
# Created: Wed Jul 29 22:55:26 2015 (-0400)
# Version: 
# Last-Updated: Sun Aug 23 06:08:47 2015 (-0400)
#           By: subha
#     Update #: 338
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
from PyQt5.QtCore import (Qt, pyqtSignal, QSettings, QPoint, QSize,
                          QFileInfo)
from PyQt5.QtWidgets import (QApplication, QTableView, QWidget, QVBoxLayout,
                             QMainWindow, QDockWidget, QFileDialog,
                             QAction, QLabel, QMdiArea)
from PyQt5.QtGui import (QIcon, QKeySequence)


from hdftreewidget import HDFTreeWidget
from hdfdatasetwidget import HDFDatasetWidget


class DataViz(QMainWindow):
    """The main application window for dataviz.

    This is an MDI application with dock displaying open HDF5 files on
    the left. Attributes of the selected item at left bottom.

    Signals
    -------

    sigOpen: Emitted when a set of files have been selected in the open
          files dialog. Sends out the list of file paths selected.
    
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
    sigOpen = pyqtSignal(list)
    sigCloseFiles = pyqtSignal()
    sigShowAttributes = pyqtSignal()
    sigShowDataset = pyqtSignal()
    sigPlotDataset = pyqtSignal()

    def __init__(self, parent=None, flags=Qt.WindowFlags(0)):
        super().__init__(parent=parent, flags=flags)
        self.readSettings()
        self.mdiArea = QMdiArea()
        self.mdiArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.mdiArea.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setCentralWidget(self.mdiArea)
        self.createActions()
        self.createMenus()
        self.createTreeDock()

    def closeEvent(self, event):
        self.writeSettings()
        event.accept()

    def readSettings(self):
        settings = QSettings('dataviz', 'dataviz')
        self.lastDir = settings.value('lastDir', '.', str)
        pos = settings.value('pos', QPoint(200, 200))
        size = settings.value('size', QSize(400, 400))
        self.move(pos)
        self.resize(size)

    def writeSettings(self):
        settings = QSettings('dataviz', 'dataviz')
        settings.setValue('lastDir', self.lastDir)
        settings.setValue('pos', self.pos())
        settings.setValue('size', self.size())

    def openFiles(self):
        filePaths, _ = QFileDialog.getOpenFileNames(self, 
                                                 'Open file(s)', self.lastDir,
                                                 'HDF5 file (*.h5 *.hdf);;All files (*)')
        if len(filePaths) == 0:
            return
        self.lastDir = QFileInfo(filePaths[-1]).dir().absolutePath()
        # TODO handle recent files
        self.sigOpen.emit(filePaths)
        
    def createActions(self):
        self.openFileAction = QAction(QIcon(), '&Open file(s)', self,
                                   shortcut=QKeySequence.Open,
                                   statusTip='Open an HDF5 file',
                                   triggered=self.openFiles)
        self.closeFileAction = QAction(QIcon(), '&Close file(s)',
                                       self,
                                       shortcut=QKeySequence(Qt.CTRL+Qt.Key_K),
                                       statusTip='Close selected files',
                                       triggered=self.sigCloseFiles)
        self.quitAction = QAction(QIcon(), '&Quit', self,
                                  shortcut=QKeySequence.Quit, 
                                  statusTip='Quit dataviz', 
                                  triggered=self.doQuit)
        self.showAttributesAction = QAction(QIcon(), 'Show attributes', self,
                                            shortcut=QKeySequence.InsertParagraphSeparator,
                                            statusTip='Show attributes',
                                            triggered=self.sigShowAttributes)
        self.showDatasetAction = QAction(QIcon(), 'Show dataset', self,
                                            shortcut=QKeySequence(Qt.CTRL+Qt.Key_Return),
                                            statusTip='Show dataset',
                                            triggered=self.sigShowDataset)
        self.plotDatasetAction = QAction(QIcon(), 'Plot dataset', self,
                                         shortcut=QKeySequence(Qt.ALT + Qt.Key_P),
                                         statusTip='Plot dataset',
                                         triggered=self.sigPlotDataset)
        


    def createMenus(self):
        self.menuBar().setVisible(True)
        self.fileMenu = self.menuBar().addMenu('&File')
        self.fileMenu.addAction(self.openFileAction)
        self.fileMenu.addAction(self.closeFileAction)
        self.fileMenu.addAction(self.quitAction)
        self.viewMenu = self.menuBar().addMenu('&View')        
        self.dataMenu = self.menuBar().addMenu('&Data')
        self.dataMenu.addAction(self.showAttributesAction)
        self.dataMenu.addAction(self.showDatasetAction)
        self.dataMenu.addAction(self.plotDatasetAction)

    def createTreeDock(self):
        self.treeDock = QDockWidget('File tree', self)
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
        self.addDockWidget(Qt.LeftDockWidgetArea, self.treeDock)
        self.viewMenu.addAction(self.treeDock.toggleViewAction())

    def addMdiChildWindow(self, widget):
        if widget is not None:
            subwin = self.mdiArea.addSubWindow(widget)
            subwin.setWindowTitle(widget.name)
            widget.show()

    def closeMdiChildWindow(self, widget):
        if widget is not None:
            for window in self.mdiArea.subWindowList():
                if window.widget() == widget:
                    window.deleteLater()

    def addPanelBelow(self, widget):
        dockWidget = QDockWidget(widget.name)
        dockWidget.setWidget(widget)
        self.addDockWidget(Qt.BottomDockWidgetArea, dockWidget)
        dockWidget.show()
        

    def doQuit(self):
        self.writeSettings()
        QApplication.instance().closeAllWindows()
        

def main():
    import sys
    from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QTreeView, QWidget)
    app = QApplication(sys.argv)
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

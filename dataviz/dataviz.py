#!/usr/bin/python3

# dataviz.py --- 
# 
# Filename: dataviz.py
# Description: 
# Author: subha
# Maintainer: 
# Created: Wed Jul 29 22:55:26 2015 (-0400)
# Version: 
# Last-Updated: Sat Aug  8 20:09:49 2015 (-0400)
#           By: subha
#     Update #: 265
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
from PyQt5.QtWidgets import (QTableView, QWidget, QVBoxLayout,
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

    open: Emitted when a set of files have been selected in the open
          files dialog. Sends out the list of file paths selected.
    
    closeFiles: Emitted when the user triggers closeFilesAction. This
                is passed on to the HDFTreeWidget which decides which
                files to close based on selection.

    showAttributes: Emitted when showAttributesAction is
                    triggered. Connected to
                    HDFTreeWidget.showAttributes function which
                    creates a widget for displaying attributes of the
                    HDF5 node of its current
                    item. HDFTreeWidget.showAttributes sends a return
                    signal `attributeWidgetCreated` with the created
                    widget so that the DataViz widget can incorporate
                    it as an mdi child window.

    showDataset: Emitted when showDatasetAction is
                 triggered. Connected to HDFTreeWidget's showDataset
                 function which creates a widget for displaying the
                 contents of the HDF5 node if it is a dataset.
                 HDFTreeWidget.showDataset sends a return signal
                 `datasetWidgetCreated` with the created widget so
                 that the DataViz widget can incorporate it as an mdi
                 child window.

    

    """
    open = pyqtSignal(list)
    closeFiles = pyqtSignal()
    showAttributes = pyqtSignal()
    showDataset = pyqtSignal()

    def __init__(self, parent=None, flags=Qt.WindowFlags(0)):
        super().__init__(parent=parent, flags=flags)
        self.readSettings()
        self.mdiArea = QMdiArea()
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
        self.open.emit(filePaths)
        
    def createActions(self):
        self.openFileAction = QAction(QIcon(), '&Open file(s)', self,
                                   shortcut=QKeySequence.Open,
                                   statusTip='Open an HDF5 file',
                                   triggered=self.openFiles)
        self.closeFileAction = QAction(QIcon(), '&Close file(s)',
                                       self,
                                       shortcut=QKeySequence(Qt.CTRL+Qt.Key_K),
                                       statusTip='Close selected files',
                                       triggered=self.closeFiles)
        self.quitAction = QAction(QIcon(), '&Quit', self,
                                  shortcut=QKeySequence.Quit, 
                                  statusTip='Quit dataviz', 
                                  triggered=QApplication.instance().closeAllWindows)
        self.showAttributesAction = QAction(QIcon(), 'Show attributes', self,
                                            shortcut=QKeySequence.InsertParagraphSeparator,
                                            statusTip='Show attributes',
                                            triggered=self.showAttributes)
        self.showDatasetAction = QAction(QIcon(), 'Show dataset', self,
                                            shortcut=QKeySequence(Qt.CTRL+Qt.Key_Return),
                                            statusTip='Show dataset',
                                            triggered=self.showDatasetFn)


    def createMenus(self):
        menuBar = self.menuBar()
        menuBar.setVisible(True)
        self.fileMenu = self.menuBar().addMenu('&File')
        self.fileMenu.addAction(self.openFileAction)
        self.fileMenu.addAction(self.closeFileAction)
        self.fileMenu.addAction(self.quitAction)
        self.viewMenu = self.menuBar().addMenu('&View')        
        self.dataMenu = self.menuBar().addMenu('&Data')
        self.dataMenu.addAction(self.showAttributesAction)
        self.dataMenu.addAction(self.showDatasetAction)

    def createTreeDock(self):
        self.treeDock = QDockWidget('File tree', self)
        self.tree = HDFTreeWidget(parent=self.treeDock)
        self.open.connect(self.tree.openFiles)
        self.tree.doubleClicked.connect(self.tree.createDatasetWidget)
        self.tree.datasetWidgetCreated.connect(self.addMdiChildWindow)
        self.tree.datasetWidgetClosed.connect(self.closeMdiChildWindow)
        self.tree.attributeWidgetCreated.connect(self.addMdiChildWindow)
        self.tree.attributeWidgetClosed.connect(self.closeMdiChildWindow)
        # pipe signals of dataviz to those of hdftree widget
        self.showAttributes.connect(self.tree.showAttributes)
        self.showDataset.connect(self.tree.showDataset)
        self.closeFiles.connect(self.tree.closeFiles)
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

    def showDatasetFn(self):
        print('Here')
        self.showDataset.emit()

    
if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QTreeView, QWidget)
    app = QApplication(sys.argv)
    window = DataViz()
    window.show()
    sys.exit(app.exec_())
    

# 
# dataviz.py ends here

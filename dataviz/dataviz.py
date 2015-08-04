#!/usr/bin/python3

# dataviz.py --- 
# 
# Filename: dataviz.py
# Description: 
# Author: subha
# Maintainer: 
# Created: Wed Jul 29 22:55:26 2015 (-0400)
# Version: 
# Last-Updated: Mon Aug  3 23:45:52 2015 (-0400)
#           By: subha
#     Update #: 189
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

    """
    open = pyqtSignal(list)
    closeFiles = pyqtSignal()

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
        self.closeFileAction = QAction(QIcon(), '&Close file(s)', self,
                                   shortcut=QKeySequence.Close,
                                   statusTip='Close selected files',
                                       triggered=self.closeFiles)

    def createMenus(self):
        menuBar = self.menuBar()
        print(menuBar)
        menuBar.setVisible(True)
        self.fileMenu = self.menuBar().addMenu('&File')
        self.fileMenu.addAction(self.openFileAction)
        self.fileMenu.addAction(self.closeFileAction)
        self.viewMenu = self.menuBar().addMenu('&View')        

    def createTreeDock(self):
        self.treeDock = QDockWidget('File tree', self)
        self.tree = HDFTreeWidget(parent=self.treeDock)
        self.open.connect(self.tree.openFiles)
        self.tree.doubleClicked.connect(self.tree.createDatasetWidget)
        self.tree.datasetWidgetCreated.connect(self.addDatasetWidget)
        self.closeFiles.connect(self.tree.closeFiles)
        self.treeDock.setWidget(self.tree)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.treeDock)
        self.viewMenu.addAction(self.treeDock.toggleViewAction())

    def addDatasetWidget(self, widget ):
        print('Received', widget)
        if widget is not None:
            self.mdiArea.addSubWindow(widget)
            widget.show()


    def quit(self):
        self.writeSettings()

    
if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QTreeView, QWidget)
    app = QApplication(sys.argv)
    window = DataViz()
    window.show()
    sys.exit(app.exec_())
    

# 
# dataviz.py ends here

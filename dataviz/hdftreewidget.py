# hdftreewidget.py --- 
# 
# Filename: hdftreewidget.py
# Description: 
# Author: subha
# Maintainer: 
# Created: Fri Jul 24 20:54:11 2015 (-0400)
# Version: 
# Last-Updated: Fri Sep 18 21:08:59 2015 (-0400)
#           By: subha
#     Update #: 539
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
"""Defines class to display HDF5 file tree.

"""

from collections import defaultdict
import numpy as np
import h5py as h5

from pyqtgraph import (QtCore, QtGui)

from pyqtgraph import parametertree as ptree

from hdftreemodel import (HDFTreeModel, EditableItem)
from hdfdatasetwidget import HDFDatasetWidget
from hdfattributewidget import HDFAttributeWidget
from datasetplot import DatasetPlot

class HDFTreeWidget(QtGui.QTreeView):
    """Convenience class to display HDF file trees. 

    HDFTreeWidget wraps an HDFTreeModel and displays it.
    In addition it allows opening multiple files from a list.

    Signals
    -------

    sigDatasetWidgetCreated(QWidget): emitted by createDatasetWidget slot
    after a new dataset widget is created with the created
    widget. This provides a way to send it back to the DataViz widget
    (top level widget and caller of the slot) for incorporation into
    the main window.

    sigDatasetWidgetClosed(QWidget): this is emitted for each of the
    widgets showing datasets under a given file tree when the file is
    closed. This allows the toplevel widget to close the corresponding
    mdi child window.

    sigAttributeWidgetCreated(QWidget): same as sigDatasetWidgetCreated but
    for the widget displaying HDF5 attributes.

    sigAttributeWidgetClosed(QWidget): same as sigDatasetWidgetClosed but
    for the widget displaying HDF5 attributes.

    sigPlotWidgetCreated(QWidget): same as sigDatasetWidgetCreated but
    for the widget displaying HDF5 dataset plots.

    sigPlotWidgetClosed(QWidget): same as sigDatasetWidgetClosed but
    for the widget displaying HDF5 dataset plots.

    """
    sigDatasetWidgetCreated = QtCore.pyqtSignal(QtGui.QWidget)
    sigDatasetWidgetClosed = QtCore.pyqtSignal(QtGui.QWidget)
    sigAttributeWidgetCreated = QtCore.pyqtSignal(QtGui.QWidget)
    sigAttributeWidgetClosed = QtCore.pyqtSignal(QtGui.QWidget)
    sigPlotWidgetCreated = QtCore.pyqtSignal(QtGui.QWidget)
    sigPlotWidgetClosed = QtCore.pyqtSignal(QtGui.QWidget)
    sigPlotParamTreeCreated = QtCore.pyqtSignal(QtGui.QWidget)

    def __init__(self, parent=None):
        super(HDFTreeWidget, self).__init__(parent)
        model = HDFTreeModel([])
        self.setModel(model)
        self.openDatasetWidgets = defaultdict(set)
        self.openAttributeWidgets = defaultdict(set)
        self.openPlotWidgets = defaultdict(set)
        self.createActions()
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.showContextMenu)        

    def createActions(self):
        self.insertDatasetAction = QtGui.QAction(QtGui.QIcon(), 'Insert dataset', self,
                                           statusTip='Create and insert a dataset under currently selected group',
                                           triggered=self.insertDataset)
        self.insertGroupAction  = QtGui.QAction(QtGui.QIcon(), 'Insert group', self,
                                           statusTip='Create and insert a group under currently selected group',
                                           triggered=self.insertGroup)
        self.deleteNodeAction = QtGui.QAction(QtGui.QIcon(), 'Delete node', self,
                                        statusTip='Delete the currently selected node.',
                                        triggered=self.deleteNode)        

    def openFiles(self, files, mode='r+'):
        """Open the files listed in argument.

        files: list of file paths. For example, output of
               QFileDialog::getOpenFileNames

        mode: string specifying open mode for h5py

        """
        for fname in files:
            self.model().openFile(fname, mode)
        
    def closeFiles(self):
        """Close the files selected in the model.

        If there are datasets in the file that are being displayed via
        a `HDFDatasetWidget`, then it emits a sigDatasetWidgetClosed
        signal with the HDFDatasetWidget as a parameter for each of
        them. Same for `HDFAttributeWidget`s.

        """
        indices = self.selectedIndexes()
        for index in indices:
            item = self.model().getItem(index)            
            filename = item.h5node.file.filename
            if self.model().closeFile(index):
                for datasetWidget in self.openDatasetWidgets[filename]:
                    self.sigDatasetWidgetClosed.emit(datasetWidget)
                self.openDatasetWidgets[filename].clear()
                for attributeWidget in self.openAttributeWidgets[filename]:
                    self.sigAttributeWidgetClosed.emit(attributeWidget)
                self.openAttributeWidgets[filename].clear()
                for plotWidget in self.openPlotWidgets[filename]:
                    self.sigPlotWidgetClosed.emit(plotWidget)
                self.openPlotWidgets[filename].clear()

    def createDatasetWidget(self, index):
        """Returns a dataset widget for specified index.

        Emits sigDatasetWidgetCreated(newWidget).

        """
        item = self.model().getItem(index)
        if (item is not None) and item.isDataset():
            # TODO maybe avoid duplicate windows for a dataset
            widget = HDFDatasetWidget(dataset=item.h5node)            
            self.openDatasetWidgets[item.h5node.file.filename].add(widget)
            self.sigDatasetWidgetCreated.emit(widget)
            
    def createAttributeWidget(self, index):
        """Creates an attribute widget for specified index.

        Emits sigAttributeWidgetCreated(newWidget)
        """
        item = self.model().getItem(index)
        if item is not None:
            # TODO maybe avoid duplicate windows for a attributes of a
            # single node
            widget = HDFAttributeWidget(node=item.h5node)            
            self.openAttributeWidgets[item.h5node.file.filename].add(widget)
            self.sigAttributeWidgetCreated.emit(widget)

    def createPlotWidget(self, index):
        """Creates an plot widget for specified index.

        Emits sigAttributeWidgetCreated(newWidget)
        """
        item = self.model().getItem(index)
        if item is not None and isinstance(item.h5node, h5.Dataset):
            widget = DatasetPlot()
            self.openPlotWidgets[item.h5node.file.filename].add(widget)
            plot, params = widget.plotLine(item.h5node)
            self.sigPlotWidgetCreated.emit(widget)
            self.sigPlotParamTreeCreated.emit(params)
            
    def showAttributes(self):
        """Create an attribute widget for currentItem"""
        self.createAttributeWidget(self.currentIndex())

    def showDataset(self):
        """Create dataset widget for currentItem"""
        self.createDatasetWidget(self.currentIndex())

    def plotDataset(self):
        """Create a PlotWidget for currentItem"""
        self.createPlotWidget(self.currentIndex())

    def insertDataset(self):        
        index = self.currentIndex()
        datasetDialog = DatasetDialog()
        ret = datasetDialog.exec_()
        if ret != QtGui.QDialog.Accepted:
            return
        params = datasetDialog.getDatasetParams()
        item = self.model().getItem(index)
        if item.isDataset():
            index = self.model().parent(index)
        self.model().insertNode(parent=index, data=params, nodeType=h5.Dataset)

    def insertGroup(self):        
        index = self.currentIndex()
        groupDialog = GroupDialog()
        ret = groupDialog.exec_()
        if ret != QtGui.QDialog.Accepted:
            return
        params = groupDialog.getParams()
        item = self.model().getItem(index)
        if item.isDataset():
            index = self.model().parent(index)
        self.model().insertNode(parent=index, data=params, nodeType=h5.Group)

    def deleteNode(self):
        index = self.currentIndex()
        choice = QtGui.QMessageBox.question(self, 'Confirm delete',
                                            'Really delete this node and all its children?',
                                            buttons=QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
        if choice == QtGui.QMessageBox.Yes:
            self.model().deleteNode(index)

    def showContextMenu(self, point):
        menu = QtGui.QMenu()
        if isinstance(self.model().getItem(self.currentIndex()), EditableItem):
            menu.addAction(self.insertDatasetAction)
            menu.addAction(self.insertGroupAction)
            menu.addAction(self.deleteNodeAction)
        menu.exec_(self.mapToGlobal(point))

class DatasetDialog(QtGui.QDialog):
    def __init__(self, parent=None):
        super(DatasetDialog, self).__init__(parent)
        self.params = ptree.Parameter.create(name='datasetParameters',
                                             title='Dataset parameters',
                                             type='group',
                                             children=[{'name': 'name',
                                                        'type': 'str',
                                                        'value': 'dataset'},
                                                       {'name': 'dtype',
                                                        'title': 'datatype',
                                                        'type': 'str',
                                                        'value': 'float'},
                                                       {'name': 'shape',
                                                        'type': 'str',
                                                        'value': '(0),'},
                                                       {'name': 'maxshape',
                                                        'type': 'str',
                                                        'value': '(None,)'},
                                                       {'name': 'chunks',
                                                        'type': 'str',
                                                        'value': 'True'}])
        layout = QtGui.QVBoxLayout()
        paramTree = ptree.ParameterTree(showHeader=False)
        paramTree.setParameters(self.params)
        self.tabWidget = QtGui.QTabWidget()
        self.tabWidget.addTab(paramTree, 'Structure')
        attrTree = ptree.ParameterTree(showHeader=False)
        self.attrs = XtensibleParam(name='attrs', title='Attributes')
        attrTree.setParameters(self.attrs)
        self.tabWidget.addTab(attrTree, 'Attributes')
        layout.addWidget(self.tabWidget)
        buttonBox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel, QtCore.Qt.Horizontal)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)
        layout.addWidget(buttonBox)
        self.setLayout(layout)
                                                        
    def getDatasetParams(self):
        values = {child.name(): child.value() for child in self.params.children()}
        values['maxshape'] = eval(values['maxshape'])
        values['chunks'] = eval(values['chunks'])
        values['shape'] = eval(values['shape'])
        values['dtype'] = eval('np.dtype({})'.format(values['dtype']))
        values['attrs'] = {ch.name(): ch.value() for ch in self.attrs.children()}
        return values


        
class GroupDialog(QtGui.QDialog):
    def __init__(self, parent=None):
        super(GroupDialog, self).__init__(parent)
        self.params = ptree.Parameter.create(name='groupParameters',
                                             title='Group attributes',
                                             type='group',
                                             children=[{'name': 'name', 'title': 'Name', 'type': 'str',
                                                        'value': 'group'},
                                                       XtensibleParam(name='attrs', title='Attributes')])
        
        layout = QtGui.QVBoxLayout()
        paramTree = ptree.ParameterTree(showHeader=False)
        paramTree.setParameters(self.params)
        layout.addWidget(paramTree)
        buttonBox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel, QtCore.Qt.Horizontal)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)
        layout.addWidget(buttonBox)
        self.setLayout(layout)
                                                        
    def getParams(self):
        values = self.params.getValues()
        opts = {'name': self.params.child('name').value(),
                'attrs': {ch.name(): ch.value() for ch in self.params.child('attrs').children()}}
        return opts


bgBrush = QtGui.QBrush(QtGui.QColor('lightsteelblue'))
class XtensibleParam(ptree.parameterTypes.GroupParameter):
    def __init__(self, **opts):
        opts['type'] = 'group'
        opts['addText'] = "Add"
        opts['addList'] = ['int', 'float', 'str']
        super(XtensibleParam, self).__init__(**opts)

    def addNew(self, typ):
        val = {'int': '0',
               'float': '0.0',
               'str': ''}[typ]
        child = self.addChild({
            'name': 'attribute',
            'type': typ,
            'value': val,
            'removable': True,
            'renamable': True,
        }, autoIncrementName=True)
        for item in child.items:
            item.setBackground(0, bgBrush)


if __name__ == '__main__':
    import sys
    app = QtGui.QApplication(sys.argv)
    window = QtGui.QMainWindow()
    widget = HDFTreeWidget()
    window.setCentralWidget(widget)
    widget.openFiles(['test.h5'], 'r+')
    window.show()
    sys.exit(app.exec_())

# 
# hdftreewidget.py ends here

#!/usr/bin/env python

# Filename: dataviz.py
# Description: 
# Author: Subhasis Ray
# Maintainer: 
# Copyright (C) 2010 Subhasis Ray, all rights reserved.
# Created: Wed Dec 15 10:16:41 2010 (+0530)
# Version: 
# Last-Updated: Sun Mar  6 14:14:15 2011 (+0530)
#           By: Subhasis Ray
#     Update #: 1169
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

# Code:

import os
import sys
import time
from datetime import datetime
import re

import numpy as np
from pysparse.sparse.spmatrix import ll_mat
import tables
from PyQt4 import Qwt5 as Qwt


ITERS = 1000

    

class UniqueListModel(QtGui.QStringListModel):
    """The model for displaying list of unique data tables.

    Ideally this should be a table model which allows for displaying
    multiple properties of each table in columns, and sorting
    according to them. But for the time being I am taking the quickest
    option.
    """
    
    def __init__(self, *args):
        QtGui.QStringList.__init__(self, *args)
        
    def setData(self, index, value, role):
        """Allow setting data only if it is not already included."""
        if index.isValid() and role == Qt.Qt.EditRole and value not in self.stringList():
            self.stringList().replace(index.row(), value.toString())
            self.emit('dataChanged(const QModelIndex&, const QModelIndex&)', index, index)
            return True
        return False
    
        
                
def train_to_cellname(trainname):
    """Extract the name of the generator cell from a spike/Vm/Ca train name"""
    return trainname[:trainname.rfind('_')]

class TraubData:
    """Data model for exploring simulation data.

    datafilename -- path of the data file

    h5f -- hdf5 file object
    """
    def __init__(self, filename):
        self.datafilename = filename
        self.h5f = None
        self.spiketrain_names = []
        self.Vm_names = []
        self.Ca_names = []
        self.simtime = None
        self.simdt = None
        self.plotdt = None
        self.timestamp = None
        
        try:
            self.h5f = tables.openFile(self.datafilename)            
        except Exception, e:
            raise e
        try:
            self.simtime = self.h5f.root._v_attrs.simtime
            self.simdt = self.h5f.root._v_attrs.simdt
            self.plotdt = self.h5f.root._v_attrs.plotdt
        except AttributeError, e:
            print e
        
        try:
            for train in self.h5f.root.spikes:
                self.spiketrain_names.append(train.name)
        except tables.NoSuchNodeError:
            print 'No node called /spikes'
        try:
            for vm_array in self.h5f.root.Vm:
                self.Vm_names.append(vm_array.name)
        except tables.NoSuchNodeError:
            print 'No node called /Vm'

        try:
            for ca_array in self.h5f.root.Ca:
                self.Ca_names.append(ca_array.name)
        except tables.NoSuchNodeError:
            print 'No node called /Ca'

            
    def get_data_by_name(self, names, datatype):
        """Return the data tables listed in names.

        If datatype is None then use the name to recognize type -
        ending with ca will be a [Ca2+] table, ending with Vm will be
        a Vm table, with spike will be a spike table.
        
        """
        ret = None
        target_node = None
        if datatype.lower() == 'ca':
            target_node = '/Ca'
        elif datatype.lower() == 'vm':
            target_node = '/Vm'
        elif datatype.lower() == 'spike':
            target_node = '/spikes'
        else:
            print 'Invalid data type: %s' % (datatype)
            return None
        ret = [self.h5f.getNode(str(target_node), str(name)) for name in names]
        return ret

    def get_data_by_re(self, pattern, datatype):
        """Returns data for cells whose name match regular expression 'pattern'"""
        ret = []
        regex = re.compile(pattern)
        if datatype == 'spike':
            target_node = '/spikes'
        elif datatype == 'Vm' or datatype == 'vm':
            target_node = '/Vm'
        elif datatype == 'Ca' or datatype == 'ca':
            target_node = '/Ca'
        else:
            raise Exception('Invalid datatype specified: %s' %(datatype))
                            
        try:
            ret = [data for data in self.h5f.getNode(target_node) if regex.match(data.name)]
        except tables.NoSuchNodeError:
            print 'No such node: %s' % (target_node)
        return ret
                
    def __del__(self):
        # I think this is somewhat redundant - pytables takes care of
        # closing remaining open files.
        print 'del called'
        if self.h5f and self.h5f.isopen:
            self.h5f.close()
            print 'closed file'


class ScrollBar(QtGui.QScrollBar):
    """Zoom scrollbar after realtime_plot example in Qwt"""
    def __init__(self, orientation, parent, minBase=None, maxBase=None):
        QtGui.QScrollBar.__init__(self, orientation, parent)
        self.init()
        if (minBase is not None) and (maxBase is not None):
            self.setBase(minBase, maxbase)
            self.moveSlider(minBase, maxBase)

    def init(self):
        self.d_inverted = self.orientation() == Qt.Qt.Vertical
        self.d_baseTicks = 1000000
        self.d_minBase = 0.0
        self.d_maxBase = 1.0
        self.moveSlider(self.d_minBase, self.d_maxBase)
        self.connect(self, QtCore.SIGNAL('sliderMoved(int)'), self.catchSliderMoved)
        self.connect(self, QtCore.SIGNAL('valueChanged(int)'), self.catchValueChanged)

    def setInverted(inverted):
        if self.d_inverted != inverted:
            self.d_inverted = inverted
            self.moveSlider(self.minSliderValue(), self.maxSliderValue())

    def isInverted(self):
        return self.d_inverted

    def setBase(self, minvalue, maxvalue):
        if (minvalue != self.d_minBase) or (maxvalue != self.d_maxBase):
            self.d_minBase = minvalue
            self.d_maxBase = maxvalue
            self.moveSlider(self.minSliderValue(), self.maxSliderValue())

    def moveSlider(self, minvalue, maxvalue):
        sliderTicks = QtCore.qRound((maxvalue - minvalue)/(self.d_maxBase - self.d_minBase)* self.d_baseTicks)

        self.blockSignals(True)
        self.setRange(sliderTicks/2, self.d_baseTicks - sliderTicks / 2)
        steps = sliderTicks/200
        if steps <= 0:
            steps = 1
        self.setSingleStep(steps)
        self.setPageStep(sliderTicks)
        tick = self.mapToTick(minvalue + (maxvalue - minvalue)/2)
        if self.isInverted():
            tick = self.d_baseTicks - tick
        self.setSliderPosition(tick)
        self.blockSignals(False)

    def minBaseValue(self):
        return self.d_minBase

    def maxBaseValue(self):
        return self.d_maxBase

    def sliderRange(self, value):
        if self.isInverted():
            value = self.d_baseTicks - value
        visibleTicks = self.pageStep()
        minvalue = self.mapFromTick(value - visibleTicks/2)
        maxvalue = self.mapFromTick(value + visibleTicks/2)
        return (minvalue, maxvalue)

    def minSliderValue(self):
        minvalue, maxvalue, = self.sliderRange(self.value())
        return minvalue
    
    def maxSliderValue(self):
        minvalue, maxvalue, = self.sliderRange(self.value())
        return maxvalue

    def mapToTick(self, v):
        return int((v- self.d_minBase) / (self.d_maxBase - self.d_minBase) * self.d_baseTicks)

    def mapFromTick(self, tick):
        return self.d_minBase + (self.d_maxBase - d_minBase) * tick / self.d_baseTick

    def catchValueChanged(self, value):
        (minvalue, maxvalue) = self.sliderRange(self, value)
        self.emit(QtCore.SIGNAL('valueChanged(QOrientation, double, double)'), self.orientation(), minvalue, maxvalue)

    def catchSliderMoved(self, value):
        (minvalue, maxvalue) = self.sliderRange(self, value)
        self.emit(QtCore.SIGNAL('sliderMoved(QOrientation, double, double)'), self.orientation(), minvalue, maxvalue)


    def extent(self):
        opt = QtGui.QStyleOptioSlider()
        opt.init(self)
        opt.setSubControls(QtGui.QStyle.SC_None)
        opt.setOrientation(self.orientation())
        opt.setMinimum(self.minimum())
        opt.setMaximum(self.maximum())
        opt.setSliderPosition(self.sliderPosition())
        opt.setSliderValue(self.value())
        opt.setSingleStep(self.singleStep())
        opt.setPageStep(self.pageStep())
        opt.setUpsideDown(self.invertedAppearance())
        if self.orientation() == Qt.Qt.Horizontal:
            opt.setState(opt.state() | QtGui.QStyle.State_Horizontal)
        return self.style().pixelMetric(QtGui.QStyle.PM_ScrollBarExtent, opt, self)

class CellListModel(QtGui.QStringListModel):
    def __init__(self, *args):
        QtGui.QStringListModel.__init__(self, *args)
        self.sister = None
        
    def set_sister(self, sister):
        self.sister = sister

    def supportedDropActions(self):
        return Qt.Qt.MoveAction

        
class CellSelectionListView(QtGui.QTableView):
    """List view subclassed to put some restrictions on drag and drop"""
    def __init__(self, *args):
        QtGui.QListView.__init__(self, *args)
        self.setDragDropMode(QtGui.QAbstractItemView.DragDrop | QtGui.QAbstractItemView.InternalMove)
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDropIndicatorShown(True)
        self.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.sister = None
        self.horizontalHeader().hide()
        
    def set_sister(self, sister):
        """Set the assocaited listview - only drag and drop from/to sister is allowed"""
        self.sister = sister
        sister.sister = self

    def dragMoveEvent(self, event):
        if event.source().objectName() == self.objectName() or event.source().objectName() == self.sister.objectName():
            event.accept()
        else:
            event.ignore()
            
    
        
class GuiModel(QtCore.QObject):
    """data_handler -- TraubData object accessing the files.

    ca_cells -- list of cells whose [Ca2+] data is available.

    vm_cells -- list of cells whose Vm data is available.

    spike_cells -- list of cells whose spiketrains are available.
    """
    def __init__(self, *args):
        QtCore.QObject.__init__(self, *args)
        self.data_handler = None
        self.selected_ca = CellListModel()
        self.selected_vm = CellListModel()
        self.selected_spikes = CellListModel()
        self.available_ca = CellListModel()
        self.available_vm = CellListModel()
        self.available_spikes = CellListModel()
        
    def openFile(self, filename):
        """Open a new data file given by filename."""
        self.data_handler = TraubData(filename)
        self.available_spikes.setStringList(self.data_handler.spiketrain_names)
        self.available_vm.setStringList(self.data_handler.Vm_names)
        self.available_ca.setStringList(self.data_handler.Ca_names)
        self.emit(QtCore.SIGNAL('file_loaded(string)'), filename)

    def select_by_re(self, pattern, datatype):
        if not self.data_handler:
            return
        data = self.data_handler.get_data_by_re(pattern, datatype)
        if datatype.lower() == 'ca':
            selected_model = self.selected_ca
            available_model = self.available_ca
        elif datatype.lower() == 'vm':
            selected_model = self.selected_vm
            available_model = self.available_vm
        elif datatype.lower() == 'spike':
            selected_model = self.selected_spikes
            available_model = self.available_spikes
        else:
            raise Exception('Invalid datatype passed: %s' % (datatype))
        selected_items = [item.name for item in data]
        selected_model.setStringList(selected_items)
        stringlist = available_model.stringList()
        row = 0
        for item in stringlist:
            if str(item) in selected_items:
                available_model.removeRows(row, 1)
            row += 1
            

        
class DataVizGui(QtGui.QMainWindow):
    def __init__(self, *args):
        QtGui.QMainWindow.__init__(self, *args)
        self.setDockOptions(self.AllowNestedDocks | self.AllowTabbedDocks | self.ForceTabbedDocks | self.AnimatedDocks)
        self.setDockNestingEnabled(True)
        self.gui_model = GuiModel()
        self.make_table_lists()
        self.plot_panel = QtGui.QTabWidget(self)
        self.setCentralWidget(self.plot_panel)
        self.spike_plot_tab = QtGui.QFrame(self.plot_panel)
        self.vm_plot_tab = QtGui.QFrame(self.plot_panel)
        self.ca_plot_tab = QtGui.QFrame(self.plot_panel)
        layout = QtGui.QHBoxLayout()        
        self.spike_plot = Qwt.QwtPlot(self.spike_plot_tab)
        # self.scrollbar = ScrollBar(Qt.Qt.Vertical, self.spike_plot)
        
        layout.addWidget(self.spike_plot)
        self.spike_plot_tab.setLayout(layout)
        layout = QtGui.QHBoxLayout()
        self.vm_plot = Qwt.QwtPlot(self.vm_plot_tab)
        layout.addWidget(self.vm_plot)
        self.vm_plot_tab.setLayout(layout)
        layout = QtGui.QHBoxLayout()        
        self.ca_plot = Qwt.QwtPlot(self.ca_plot_tab)
        layout.addWidget(self.ca_plot)
        self.ca_plot_tab.setLayout(layout)
        
        self.plot_panel.addTab(self.spike_plot_tab, 'Spikes')
        self.plot_panel.addTab(self.vm_plot_tab, 'Vm')
        self.plot_panel.addTab(self.ca_plot_tab, '[Ca2+]')

        self.make_actions()
        self.make_menu()
        self.toolbar = self.make_toolbar()
        
    def make_actions(self):
        self.fopen_action = QtGui.QAction(self.tr('&Open'), self)
        self.connect(self.fopen_action, QtCore.SIGNAL('triggered()'), self.popup_fopen)
        self.quit_action = QtGui.QAction(self.tr('&Quit'), self)
        self.connect(self.quit_action, QtCore.SIGNAL('triggered()'), self.do_quit)
        self.show_available_tables_action = QtGui.QAction(self.tr('Show &Available Tables'), self)
        self.show_selected_tables_action = QtGui.QAction(self.tr('Show &Selected Tables'), self)             
        self.show_available_ca_action = QtGui.QAction(self.tr('Show available Ca tables'), self)
        self.show_available_vm_action = QtGui.QAction('Show available Vm tables', self)
        self.show_available_spike_action = QtGui.QAction('Show available spike tables', self)
        self.show_selected_ca_action = QtGui.QAction('Show selected Ca tables', self)
        self.show_selected_vm_action = QtGui.QAction('Show selected Vm tables', self)
        self.show_selected_spike_action = QtGui.QAction('Show selected spike tables', self)
        self.select_by_regex_action = QtGui.QAction('Select by regex', self)
        self.plot_action = QtGui.QAction('Plot', self)
        self.connect(self.plot_action, QtCore.SIGNAL('triggered()'), self.do_plot)
        
    def make_toolbar(self):
        self.toolbar = self.addToolBar('ToolBar')
        self.regex_form = QtGui.QLineEdit('')
        self.toolbar.addWidget(self.regex_form)
        self.datatype_combo = QtGui.QComboBox(self.toolbar)
        self.datatype_combo.addItem('Ca')
        self.datatype_combo.addItem('Vm')
        self.datatype_combo.addItem('spike')
        self.toolbar.addWidget(self.datatype_combo)
        self.toolbar.addAction(self.select_by_regex_action)
        self.toolbar.addAction(self.plot_action)
        
    def make_menu(self):
        self.file_menu = QtGui.QMenu('&File', self)
        self.file_menu.addAction(self.fopen_action)
        self.file_menu.addAction(self.quit_action)
        self.view_menu = QtGui.QMenu('&View', self)
        self.view_menu.addAction(self.show_available_tables_action)
        self.view_menu.addAction(self.show_selected_tables_action)
        self.view_menu.addAction(self.show_available_spike_action)
        self.view_menu.addAction(self.show_available_vm_action)
        self.view_menu.addAction(self.show_available_ca_action)
        self.view_menu.addAction(self.show_selected_spike_action)
        self.view_menu.addAction(self.show_selected_vm_action)
        self.view_menu.addAction(self.show_selected_ca_action)
        self.menuBar().addMenu(self.file_menu)
        self.menuBar().addMenu(self.view_menu)
        
    def make_table_lists(self):
        self.selected_ca_view = CellSelectionListView(self)
        self.selected_vm_view = CellSelectionListView(self)
        self.selected_spikes_view = CellSelectionListView(self)
        self.available_ca_view = CellSelectionListView(self)
        self.available_vm_view = CellSelectionListView(self)
        self.available_spikes_view = CellSelectionListView(self)
        self.selected_ca_view.set_sister(self.available_ca_view)
        self.selected_vm_view.set_sister(self.available_vm_view)
        self.selected_spikes_view.set_sister(self.available_spikes_view)
        self.selected_ca_view.setObjectName('selected_ca')
        self.selected_vm_view.setObjectName('selected_vm')
        self.selected_spikes_view.setObjectName('selected_spikes')
        self.available_ca_view.setObjectName('available_ca')
        self.available_vm_view.setObjectName('available_vm')
        self.available_spikes_view.setObjectName('available_spikes')

        self.selected_ca_view.setModel(self.gui_model.selected_ca)
        self.selected_vm_view.setModel(self.gui_model.selected_vm)
        self.selected_spikes_view.setModel(self.gui_model.selected_spikes)
        self.available_ca_view.setModel(self.gui_model.available_ca)
        self.available_vm_view.setModel(self.gui_model.available_vm)
        self.available_spikes_view.setModel(self.gui_model.available_spikes)
        self.tables_docks = []
        self.selected_data_views = [self.selected_ca_view, self.selected_vm_view,
                 self.selected_spikes_view]
        self.available_data_views = [self.available_ca_view,
                 self.available_vm_view, self.available_spikes_view]
        for view in self.selected_data_views + self.available_data_views:
            self.tables_docks.append(QtGui.QDockWidget(view.objectName(), self))
            self.tables_docks[-1].setWidget(view)
            if view.objectName().startsWith('selected'):
                self.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.tables_docks[-1])
            else:
                self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.tables_docks[-1])
                
        
    def popup_fopen(self):
        file_dialog = QtGui.QFileDialog(self)
        file_dialog.setFileMode(QtGui.QFileDialog.ExistingFile)
        file_dialog.setFilter(self.tr('hdf5(*.h5 *.hd5 *.hdf5);;All files(*)'))
        if file_dialog.exec_():
            filenames = file_dialog.selectedFiles()
            self.gui_model.openFile(str(filenames[0]))
            self.connect(self.select_by_regex_action, QtCore.SIGNAL('triggered()'), self.select_by_re)
            
    def select_by_re(self):
        regex = str(self.regex_form.text())
        datatype = str(self.datatype_combo.currentText())
        self.gui_model.select_by_re(regex, datatype)

    def do_plot(self):
        self.plot_spike_raster()
        self.plot_vm()
        self.plot_ca()

    def plot_spike_raster(self):
        cellnames = self.gui_model.selected_spikes.stringList()
        t1 = datetime.now()
        data = self.gui_model.data_handler.get_data_by_name(cellnames, 'spike')
        t2 = datetime.now()
        delt = t2 - t1
        print 'Time to read data:', delt.seconds + delt.microseconds * 1e-6
        ii = 0
        self.spike_plot.clear()
        t1 = datetime.now()
        for table in data:
            ii += 1
            curve = Qwt.QwtPlotCurve(table.name)
            #curve.setStyle(Qwt.QwtPlotCurve.NoCurve)
            if ii % 2 == 0:
                pen = Qt.QPen(Qt.Qt.red, 1)
            else:
                pen = Qt.QPen(Qt.Qt.blue, 1)
            curve.setSymbol(Qwt.QwtSymbol(Qwt.QwtSymbol.VLine, Qt.QBrush(), pen, Qt.QSize(7, 7)))
            curve.setPen(pen)            
            curve.setData(np.array(table), np.ones(len(table))*ii)            
            curve.attach(self.spike_plot)
        self.spike_plot.replot()
        t2 = datetime.now()
        delt = t2 - t1
        print 'Time to plot data:', delt.seconds + delt.microseconds * 1e-6

    def plot_vm(self):
        cellnames = self.gui_model.selected_vm.stringList()
        data = self.gui_model.data_handler.get_data_by_name(cellnames, 'vm')
        self.vm_plot.clear()
        ii = 0
        for table in data:
            ii += 1
            curve = Qwt.QwtPlotCurve(table.name)
            # curve.setStyle(Qwt.QwtPlotCurve.NoCurve)
            # curve.setSymbol(Qwt.QwtSymbol(Qwt.QwtSymbol.VLine, Qt.QBrush(), Qt.QPen(Qt.Qt.red, 1), Qt.QSize(7, 7)))
            curve.setData(np.linspace(0, self.gui_model.data_handler.simtime, len(table)), np.array(table))            
            curve.attach(self.vm_plot)
        self.vm_plot.replot()
            
    def plot_ca(self):
        cellnames = self.gui_model.selected_ca.stringList()
        data = self.gui_model.data_handler.get_data_by_name(cellnames, 'ca')
        self.ca_plot.clear()
        ii = 0
        for table in data:
            ii += 1
            curve = Qwt.QwtPlotCurve(table.name)
            # curve.setStyle(Qwt.QwtPlotCurve.NoCurve)
            # curve.setSymbol(Qwt.QwtSymbol(Qwt.QwtSymbol.VLine, Qt.QBrush(), Qt.QPen(Qt.Qt.red, 1), Qt.QSize(7, 7)))
            curve.setData(np.linspace(0, self.gui_model.data_handler.simtime, len(table)), np.array(table))            
            curve.attach(self.ca_plot)
        self.ca_plot.replot()

    def do_quit(self):
        print 'Quitting'
        if self.gui_model.data_handler:
            del self.gui_model.data_handler
        QtGui.qApp.quit()

            


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    QtGui.qApp = app
    # mainwin = DataVizGui()
    mainwin = QtGui.QMainWindow()
    handle = h5py.File('data/data_20110215_112900_1335.h5', 'r')
    tree = H5TreeWidget(mainwin)    
    tree.addH5Handle(handle)
    mainwin.setCentralWidget(tree)
    mainwin.show()
    app.exec_()
# 
# dataviz.py ends here

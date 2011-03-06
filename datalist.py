#!/usr/bin/env python

# Filename: dataviz.py
# Description: 
# Author: Subhasis Ray
# Maintainer: 
# Copyright (C) 2010 Subhasis Ray, all rights reserved.
# Created: Wed Dec 15 10:16:41 2010 (+0530)
# Version: 
# Last-Updated: Sun Mar  6 14:00:42 2011 (+0530)
#           By: Subhasis Ray
#     Update #: 1425
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
# 2011-03-05 19:10:31 (+0530) -- tested the model and view classes
# UniqueListModel and UniqueListView for allowing only unique
# tables.
#
# The datatables are compared as strings, so we should use filename as
# part of the item identity. But I just realized that for a fullproof
# code, we need to have the file path in every item, otherwise, how do
# we discriminate between data_array_A in file X and data_array_B in
# file Y? What about the same in files /home/subha/X and
# /home/guest/X? So I need a special listwidgetitem.
#
# 2011-03-06 13:46:55 (+0530) I tested the code this morning and
# realized that handling of unix style file path was not correct. I
# had misunderstood the QString.right() function. Also, there was this
# issue with setting data. I was setting display role to be the
# trimmed table name and tooltip role to be the full path. But the
# actual data in the string list of the model is set via display
# role. Just overriding the data() function to return trimmed table
# name for displayrole is sufficient. The previous commit contains
# these corrections.

# Code:


import sys


from PyQt4 import QtGui, QtCore, Qt


ITERS = 1000




class UniqueListModel(QtGui.QStringListModel):
    """The model for displaying list of unique data tables.

    Ideally this should be a table model which allows for displaying
    multiple properties of each table in columns, and sorting
    according to them. But for the time being I am taking the quickest
    option.
    """
    
    def __init__(self, *args):
        QtGui.QStringListModel.__init__(self, *args)        

    def supportedDropActions(self):
        return Qt.Qt.MoveAction | Qt.Qt.CopyAction
    
    def flags(self, index):
        defaults = Qt.Qt.ItemIsSelectable | Qt.Qt.ItemIsEnabled
        if index.isValid():
            return Qt.Qt.ItemIsDragEnabled | defaults
        else:
            return Qt.Qt.ItemIsDropEnabled | defaults

    def data(self, index, role):
        text = self.stringList()[index.row()]
        # print text
        if role == Qt.Qt.DisplayRole:
            tname_start = text.lastIndexOf('/')        
            table_name = text.mid(tname_start+1)
            return table_name
        elif role == Qt.Qt.ToolTipRole:
            return text
        else:
            return QtGui.QStringListModel.data(self, index, role)

    def dropMimeData(self, data, action, row, column, parent):
        if not data.hasFormat('application/x-qabstractitemmodeldatalist'):
            return False
        bytearray = data.data('application/x-qabstractitemmodeldatalist')
        data_items = self.decode_data(bytearray)
        if action == Qt.Qt.MoveAction:
            QtGui.QStringListModel.dropMimeData(self,data, action, row, column, parent)
            return True
        if action == Qt.Qt.CopyAction:
            unique_entries = []
            for item in data_items:
                table_path = item[Qt.Qt.ToolTipRole].toString()
                print 'table path:', table_path
                if table_path in self.stringList():
                    print table_path, 'already in'
                    continue
                unique_entries.append(table_path)
            if unique_entries:
                if row < 0 or row >= self.rowCount():
                    row = self.rowCount()
                self.insertRows(row, len(unique_entries))
                for ii in range(len(unique_entries)):
                    tname_start = unique_entries[ii].lastIndexOf('/')
                    table_name = unique_entries[ii].mid(tname_start+1)
                    print 'setting data for row', row + ii, ':', unique_entries[ii]
                    self.setData(self.index(row + ii), QtCore.QVariant(unique_entries[ii]))
            # self.emit(QtCore.SIGNAL('dataChanged(const QModelIndex&, const QModelIndex&)'), self.index(row), self.index(row+len(unique_entries)))
                return True
            return False
        
        # if text in self.stringList():
        #     return False
        # else:
        #     return QtGui.QStringListModel.dropMimeData(self, data, action, row, column, parent)
        
    def decode_data(self, bytearray):
        # When dragging from an object of a class inheriting QAbstractItemModel,
        # the data contains a QMap. See: http://diotavelli.net/PyQtWiki/Handling%20Qt%27s%20internal%20item%20MIME%20type
        #
        # QByteArray encoded = qMimeData->data("application/x-qabstractitemmodeldatalist");
        # QDataStream stream(&encoded, QIODevice::ReadOnly);
        #
        # while (!stream.atEnd())
        # {
        #     int row, col;
        #     QMap<int,  QVariant> roleDataMap;
        #     stream >> row >> col >> roleDataMap;
        #
        #     /* do something with the data */
        # }
        data = []
        item = {}
        ds = QtCore.QDataStream(bytearray)
        while not ds.atEnd():
            row = ds.readInt32()
            column = ds.readInt32()
            mapitems = ds.readInt32()
            for ii in range(mapitems):
                key = ds.readInt32()
                value = QtCore.QVariant()
                ds >> value
                item[Qt.Qt.ItemDataRole(key)] = value
            data.append(item)
        return data
        
class UniqueListView(QtGui.QListView):
    def __init__(self, *args):
        QtGui.QListView.__init__(self, *args)
        self.setDragDropOverwriteMode(False)
        self.allowedDropSources = set()
        self.allowedDropSources.add(self)

    def addAllowedDropSources(self, widget):
        self.allowedDropSources.add(widget)
        
    def dropEvent(self, event):
        # print event.source()
        # for item in self.allowedDropSources:
        #     print 'Allowd sources: ', item
        #     print event.source() == item
        if event.source() in self.allowedDropSources:
            if event.source() == self:
                event.setDropAction(Qt.Qt.MoveAction)
            QtGui.QListView.dropEvent(self, event)
            
if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    QtGui.qApp = app
    # mainwin = DataVizGui()
    mainwin = QtGui.QMainWindow()
    frame = QtGui.QFrame(mainwin)
    mainwin.setCentralWidget(frame)
    data1 = QtCore.QStringList(['/p/q/r/a', '/mn/b', '/ij/c', '/zx/d'])
    model1 = UniqueListModel(data1)
    view1 = UniqueListView(frame)
    view1.setModel(model1)
    view1.setDragDropMode(QtGui.QAbstractItemView.DragDrop | QtGui.QAbstractItemView.InternalMove)
    view1.setAcceptDrops(True)
    view1.setDragEnabled(True)
    view1.setDropIndicatorShown(True)
    view1.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
 
    data2 = QtCore.QStringList(['/ij/c', '/yz/d', 'e', 'f'])
    model2 = UniqueListModel(data2)
    view2 = UniqueListView(frame)
    view2.setModel(model2)
    view2.setDragDropMode(QtGui.QAbstractItemView.DragDrop | QtGui.QAbstractItemView.InternalMove)
    view2.setAcceptDrops(True)
    view2.setDragEnabled(True)
    view2.setDropIndicatorShown(True)
    view2.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
    view1.addAllowedDropSources(view2)
    view2.addAllowedDropSources(view1)

    layout = QtGui.QHBoxLayout(frame)
    layout.addWidget(view1)
    layout.addWidget(view2)
    mainwin.setCentralWidget(frame)
    mainwin.show()
    app.exec_()
# 
# dataviz.py ends here

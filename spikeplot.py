# spikeplot.py --- 
# 
# Filename: spikeplot.py
# Description: 
# Author: Subhasis Ray
# Maintainer: 
# Copyright (C) 2010 Subhasis Ray, all rights reserved.
# Created: Tue Mar  8 16:21:44 2011 (+0530)
# Version: 
# Last-Updated: Wed Mar  9 16:50:46 2011 (+0530)
#           By: Subhasis Ray
#     Update #: 112
# URL: 
# Keywords: 
# Compatibility: 
# 
# 

# Commentary: 
# 
# This is for plotting spike trains.
# 
# 

# Change log:
# 
# 
# 

# Code:

from PyQt4 import Qt, QtCore, QtGui
from PyQt4 import Qwt5 as Qwt
import numpy

class SpikePlotWidget(QtGui.QWidget):
    def __init__(self, *args):
        QtGui.QWidget.__init__(self, *args)
        layout = QtGui.QHBoxLayout()
        self.plot = Qwt.QwtPlot()
        layout.addWidget(self.plot)
        self.setLayout(layout)
        self.path_curve_dict = {}

    def addPlotCurve(self, path, data, color):
        """Adds or updates a curve in the plot.

        If the curve is already there, this function will set the
        colour and data."""
        try:
            curve = self.path_curve_dict[path]
        except KeyError:
            curve = Qwt.QwtPlotCurve(path)
            curve.attach(self.plot)
            self.path_curve_dict[path] = curve
        curve.setData(data, numpy.ones(len(data))*(1 + len(self.path_curve_dict.keys())))
        pen = Qt.QPen(color, 1)
        curve.setPen(pen)
        curve.setStyle(Qwt.QwtPlotCurve.NoCurve)
        curve.setSymbol(Qwt.QwtSymbol(Qwt.QwtSymbol.VLine, Qt.QBrush(), pen, Qt.QSize(7, 7)))
        self.plot.replot()

    def addPlotCurveList(self, pathlist, datalist, colorlist):
        """Adds or updates a list of curves in the plot.

        If the curves (each identified by the path of the table it
        plots) are already there, this function will set the colour
        and data.

        The colorlist need not be same length as the datalist. The
        colors are repeated once the list is exhausted.
        """
        data_iter = iter(datalist)                
        path_iter = iter(pathlist)
        if len(datalist) != len(pathlist):
            raise Exception('data list and path list must be of same length!')
        try:
            color_iter = iter(colorlist)
        except TypeError:
            color_iter = None
            
        for ii in range(len(datalist)):
            data = datalist[ii]
            path = pathlist[ii]
            if color_iter is not None:
                color = colorlist[ii % len(colorlist)]

            try:            
                curve = self.path_curve_dict[path]
            except KeyError:
                curve = Qwt.QwtPlotCurve(path)
                curve.attach(self.plot)
                self.path_curve_dict[path] = curve
            pen = Qt.QPen(color, 1)
            curve.setPen(pen)
            curve.setStyle(Qwt.QwtPlotCurve.NoCurve)
            curve.setSymbol(Qwt.QwtSymbol(Qwt.QwtSymbol.VLine, Qt.QBrush(), pen, Qt.QSize(7, 7)))
            curve.setData(data, numpy.ones(len(data))*(1 + len(self.path_curve_dict.keys())))
        self.plot.replot()

from numpy import random        
import sys
if __name__ == '__main__':
    app = QtGui.QApplication([])
    QtGui.qApp = app
    datalist = []
    colorlist = []
    pathlist = ['/a/b/c', '/c/d', '/e/f', '/g']
    for ii in pathlist:
        datalist.append(random.rand(1000))
    colorlist = [Qt.Qt.red, Qt.Qt.green, Qt.Qt.blue]
    
    widget = SpikePlotWidget()
    widget.addPlotCurve('test', datalist[0], Qt.Qt.cyan)
    widget.addPlotCurveList(pathlist, datalist, colorlist)
    widget.show()
    sys.exit(app.exec_())

# 
# spikeplot.py ends here

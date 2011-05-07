# plotwidget.py --- 
# 
# Filename: plotwidget.py
# Description: 
# Author: Subhasis Ray
# Maintainer: 
# Copyright (C) 2010 Subhasis Ray, all rights reserved.
# Created: Tue Apr 12 10:54:53 2011 (+0530)
# Version: 
# Last-Updated: Sat May  7 00:13:09 2011 (+0530)
#           By: Subhasis Ray
#     Update #: 64
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

# Code:

from PyQt4 import Qt, QtCore, QtGui
from PyQt4 import Qwt5 as Qwt
import numpy 

class PlotWidget(Qwt.QwtPlot):
    def __init__(self, *args):
        Qwt.QwtPlot.__init__(self, *args)
        self.path_curve_dict = {}
        self.__colors = [Qt.Qt.red, Qt.Qt.green, Qt.Qt.blue]
        self.__nextColor = 0

    def nextColor(self):
        ret = self.__colors[self.__nextColor]
        self.__nextColor = (1 + self.__nextColor) % len(self.__colors)
        return ret

    def setColotList(self, colotList):
        self.__colors = colorList
        self.__nextColor = 0
        
    def addPlotCurveList(self, pathlist, datalist, colorlist=None, mode='curve'):
        """mode is either curve or raster. just for the defaults for continuous/spiketrain data.

        will give tools for finer manipulations."""
        if len(datalist) != len(pathlist):
            raise Exception('datalist and pathlist must have same length.')
        for ii in range(len(datalist)):
            data = datalist[ii]
            path = pathlist[ii]
            if colorlist is not None:
                color = colorlist[ii % len(colorlist)]
            else:
                color = self.nextColor()
            try:
                curve = self.path_curve_dict[path]
            except KeyError:
                curve = Qwt.QwtPlotCurve(path)
                curve.attach(self)
                self.path_curve_dict[path] = curve
            pen = Qt.QPen(color, 1)
            curve.setPen(pen)
            if mode == 'raster':
                curve.setStyle(curve.NoCurve)
                curve.setSymbol(Qwt.QwtSymbol(Qwt.QwtSymbol.VLine, Qt.QBrush(), pen, Qt.QSize(7,7)))
                # n-th entry in data list to be plotted at y = n+1 (counting from 0)
                if (isinstance(data, tuple) or isinstance(data, list)) and len(data) == 2:
                    curve.setData(data[1], numpy.ones(len(data[1])) * (1 + len(self.path_curve_dict.keys())))
                else:
                    curve.setData(data, numpy.ones(len(data)) * (1 + len(self.path_curve_dict.keys())))
            else:
                if (isinstance(data, tuple) or isinstance(data, list)) and len(data) == 2:
                    curve.setData(data[0], data[1])
                else:
                    xdata = numpy.linspace(0, len(data), len(data))
                    curve.setData(xdata, data)
        self.replot()
# 
# plotwidget.py ends here

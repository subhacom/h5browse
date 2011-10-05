# plotwidget.py --- 
# 
# Filename: plotwidget.py
# Description: 
# Author: Subhasis Ray
# Maintainer: 
# Copyright (C) 2010 Subhasis Ray, all rights reserved.
# Created: Tue Apr 12 10:54:53 2011 (+0530)
# Version: 
# Last-Updated: Wed Oct  5 16:30:37 2011 (+0530)
#           By: Subhasis Ray
#     Update #: 151
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
        self.curve_path_dict = {}
        self.__colors = [Qt.Qt.red, Qt.Qt.green, Qt.Qt.blue, Qt.Qt.magenta, Qt.Qt.darkCyan, Qt.Qt.black]
        self.__nextColor = 0
        self.enableAxis(2)
        self.enableAxis(0)
        self.setAxisTitle(2, 'Time (second)')
        legend = Qwt.QwtLegend()
        legend.setItemMode(Qwt.QwtLegend.CheckableItem)
        self.insertLegend(legend, Qwt.QwtPlot.TopLegend)
        self.zoomer = Qwt.QwtPlotZoomer(Qwt.QwtPlot.xBottom,
                                   Qwt.QwtPlot.yLeft,
                                   Qwt.QwtPicker.DragSelection,
                                   Qwt.QwtPicker.AlwaysOff,
                                   self.canvas())
        self.zoomer.setRubberBandPen(QtGui.QPen(Qt.Qt.black))
        self.zoomer.setTrackerPen(QtGui.QPen(Qt.Qt.black))
        self.zoomer.initKeyPattern()        
        self.zoomer.initMousePattern(2)
        pattern = [
            Qwt.QwtEventPattern.MousePattern(Qt.Qt.LeftButton,
                                             Qt.Qt.NoModifier),
            Qwt.QwtEventPattern.MousePattern(Qt.Qt.MidButton,
                                             Qt.Qt.NoModifier),
            Qwt.QwtEventPattern.MousePattern(Qt.Qt.RightButton,
                                             Qt.Qt.NoModifier),
            Qwt.QwtEventPattern.MousePattern(Qt.Qt.LeftButton,
                                             Qt.Qt.ShiftModifier),
            Qwt.QwtEventPattern.MousePattern(Qt.Qt.MidButton,
                                             Qt.Qt.ShiftModifier),
            Qwt.QwtEventPattern.MousePattern(Qt.Qt.RightButton,
                                             Qt.Qt.ShiftModifier),
            ]
        self.zoomer.setMousePattern(pattern)


    def clearZoomStack(self):
        """Auto scale and clear the zoom stack
        """
        self.setAxisAutoScale(Qwt.QwtPlot.xBottom)
        self.setAxisAutoScale(Qwt.QwtPlot.yLeft)
        self.replot()
        self.zoomer.setZoomBase()
        

    def nextColor(self):
        ret = self.__colors[self.__nextColor]
        self.__nextColor = (1 + self.__nextColor) % len(self.__colors)
        return ret

    def setColorList(self, colorList):
        self.__colors = colorList
        self.__nextColor = 0

    def showLegend(self, show):
        if show:
            legend = Qwt.QwtLegend()
            legend.setItemMode(Qwt.QwtLegend.CheckableItem)
            self.insertLegend(legend, Qwt.QwtPlot.TopLegend)
        else:
            self.insertLegend(None)
        self.replot()
            
    def editLegendText(self):
        for item in self.itemList():
            widget = self.legend().find(item)
            if isinstance(widget, Qwt.QwtLegendItem) and widget.isChecked():
                editDialog = QtGui.QInputDialog()
                editDialog.setLabelText('Enter new curve label')
                editDialog.setInputMode(QtGui.QInputDialog.TextInput)
                editDialog.setTextValue(widget.text().text())
                if editDialog.exec_() == QtGui.QDialog.Accepted:
                    widget.setText(Qwt.QwtText(editDialog.textValue()))
                    item.setTitle(Qwt.QwtText(editDialog.textValue()))
                    widget.setChecked(False)

    def reconfigureSelectedCurves(self, pen, symbol, style, attribute):
        """Reconfigure the selected curves to use pen for line and
        symbol for marking the data points."""
        print 'Reconfiguring slected plots'
        for item in self.itemList():
            widget = self.legend().find(item)
            if isinstance(widget, Qwt.QwtLegendItem) and widget.isChecked():
                item.setPen(pen)
                item.setSymbol(symbol)
                item.setStyle(style)
                item.setCurveAttribute(attribute)
        self.replot()
        
    def toggleSelectedCurves(self):
        for item in self.itemList():
            widget = self.legend().find(item)
            if isinstance(widget, Qwt.QwtLegendItem) and widget.isChecked():
                item.setVisible(not item.isVisible())
        self.replot()

    def getSelectedCurves(self):
        ret = []
        for item in self.itemList():
            if item.legendItem().isChecked():
                ret.append(item)
        return ret

    def showAllCurves(self):
        for item in self.itemList():
            if isinstance(item, Qwt.QwtPlotCurve):
                print item
                item.setVisible(True)
        self.replot()

    def setLineStyleSelectedCurves(self, style=Qwt.QwtPlotCurve.NoCurve):        
        for item in self.itemList():
            widget = self.legend().find(item)
            if isinstance(widget, Qwt.QwtLegendItem) and widget.isChecked():
                item.setStyle(style)
        self.replot()

    def fitSelectedCurves(self):
        for item in self.itemList():
            if item.legendItem().isChecked():
                item.setCurveAttribute(item.Fitted)
                fitter = Qwt.QwtSplineCurveFitter()
                fitter.setSplineSize(10)
                item.setCurveFitter(fitter)
        self.replot()
                
    def setSymbol(self, 
                       symbolStyle=None, 
                       brushColor=None, brushStyle=None, 
                       penColor=None, penWidth=None, penStyle=None, 
                       symbolHeight=None, symbolWidth=None):
        """Set the symbol used in plotting.

        This function gives overly flexible access to set the symbol
        of all the properties of the currently selected curves. If any
        parameter is left unspecified, the existing value of that
        property of the symbol is maintained.

        TODO: create a little plot-configuration widget to manipulate each
        property of the selected curves visually. That should replace setting setSymbol amd setLineStyle.

        """
        for item in self.itemList():
            widget = self.legend().find(item)
            if isinstance(widget, Qwt.QwtLegendItem) and widget.isChecked():
                oldSymbol = item.symbol()
                if symbolStyle is None:
                    symbolStyle = oldSymbol.style()
                if brushColor is None:
                    brushColor = oldSymbol.brush().color()
                if brushStyle is None:
                    brushStyle = oldSymbol.brush().style()
                if penColor is None:
                    penColor = oldSymbol.pen().color()
                if penWidth is None:
                    penWidth = oldSymbol.pen().width()
                if penStyle is None:
                    penStyle = oldSymbol.pen().style()
                if symbolHeight is None:
                    symbolHeight = oldSymbol.size().height()
                if symbolWidth is None:
                    symbolWidth = oldSymbol.size().width()
                pen = QtGui.QPen(penColor, penWidth, penStyle)
                symbol = Qwt.QwtSymbol(symbolStyle, oldSymbol.brush(), pen, QtCore.QSize(width, height)) 
                item.setSymbol(symbol)
        self.replot()

    def alignScales(self):
        self.canvas().setFrameStyle(QtGui.QFrame.Box | QtGui.QFrame.Plain)
        self.canvas().setLineWidth(1)
        for ii in range(Qwt.QwtPlot.axisCnt):
            scaleWidget = self.axisWidget(ii)
            if scaleWidget:
                scaleWidget.setMargin(0)
            scaleDraw = self.axisScaleDraw(ii)
            if scaleDraw:
                scaleDraw.enableComponent(Qwt.QwtAbstractScaleDraw.Backbone, False)

    def savePlotImage(self, filename):
        pixmap = QtGui.QPixmap(1024, 768)
        pixmap.fill(Qt.Qt.white)
        prnfilter = Qwt.QwtPlotPrintFilter()
        options = prnfilter.PrintAll
        prnfilter.setOptions(options)
        self.print_(pixmap, prnfilter)
        pixmap.save(filename)
                
    def addPlotCurveList(self, pathlist, datalist, simtime=1.0, colorlist=None, mode='curve'):
        """mode is either curve or raster. just for the defaults for
        continuous/spiketrain data.  will give tools for finer
        manipulations."""
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
                self.curve_path_dict[curve] = path
            pen = Qt.QPen(color, 1)
            curve.setPen(pen)
            curve.setTitle(path)
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
                    xdata = numpy.linspace(0, simtime, len(data))
                    curve.setData(xdata, data)
        self.clearZoomStack()
# 
# plotwidget.py ends here

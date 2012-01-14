# plotwidget.py --- 
# 
# Filename: plotwidget.py
# Description: 
# Author: Subhasis Ray
# Maintainer: 
# Copyright (C) 2010 Subhasis Ray, all rights reserved.
# Created: Tue Apr 12 10:54:53 2011 (+0530)
# Version: 
# Last-Updated: Sat Jan 14 16:36:09 2012 (+0530)
#           By: subha
#     Update #: 535
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

from collections import defaultdict
from PyQt4 import Qt, QtCore, QtGui
from PyQt4 import Qwt5 as Qwt
import numpy

class SpectrogramData(Qwt.QwtRasterData):
    def __init__(self, datalist):
        self.datalist = datalist
        maxx = 0
        min_dx = 1e9
        for (x, y) in datalist:
            if (x[-1] -x[-2]) < min_dx:
                min_dx = (x[-1] -x[-2])
            if x[-1] > maxx:
                maxx = x[-1]
        new_list = []
        self.xvalues = numpy.arange(0, maxx, min_dx)        
        self.yvalues = numpy.zeros((len(datalist), len(self.xvalues)))
        self.ymin = 1e9
        self.ymax = -1e9
        index = 0
        for (x, y) in datalist:
            if len(x) != len(self.xvalues):
                self.yvalues[index, :] = numpy.interp(self.xvalues, x, y, 0.0, 0.0)
            else:
                self.yvalues[index, :] = y[:]
            tmp_min = min(self.yvalues[index])
            tmp_max = max(self.yvalues[index])
            if tmp_min < self.ymin:
                self.ymin = tmp_min
            if tmp_max > self.ymax:
                self.ymax = tmp_max            
            index += 1

        Qwt.QwtRasterData.__init__(self, Qt.QRectF(self.xvalues[0], 0, self.xvalues[-1], len(datalist)))

    def copy(self):
        return self
    
    def range(self):
        print 'Range', self.ymin, self.ymax
        return Qwt.QwtDoubleInterval(self.ymin, self.ymax)

    def value(self, x, y):
        if x < 0 or x > self.xvalues[-1] or y < 0 or y >= self.yvalues.shape[0]:
            return 0
        index = int(x/(self.xvalues[-1] - self.xvalues[-2]))
        ret = self.yvalues[int(y), index]
        return ret

    def numrows(self):
        return len(self.yvalues)

    def interval(self, axis):
        if axis == Qwt.QwtPlot.xBottom:
            return Qwt.QwtInterval(self.xvalues[0], self.xvalues[-1])
        elif axis == Qwt.QwtPlot.yLeft:
            return Qwt.QwtInterval(self.ymin, self.ymax)

class PlotWidget(Qwt.QwtPlot):
    def __init__(self, *args):
        Qwt.QwtPlot.__init__(self, *args)
        self.path_curve_dict = defaultdict(list)
        self.curve_path_dict = {}
        self.__colors = [Qt.Qt.red, Qt.Qt.green, Qt.Qt.blue, Qt.Qt.magenta, Qt.Qt.darkCyan, Qt.Qt.black]
        self.__nextColor = 0
        self.__overlay = True
        self.enableAxis(2)
        self.enableAxis(0)
        self.setAxisTitle(2, 'Time (second)')
        self.setCanvasBackground(Qt.Qt.white)
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
        # self.zoomer.setEnabled(False)
        self.canvas().installEventFilter(self)
        self.picker = Qwt.QwtPlotPicker(Qwt.QwtPlot.xBottom,
                                        Qwt.QwtPlot.yLeft,
                                        Qwt.QwtPicker.PointSelection | Qwt.QwtPicker.DragSelection,                                        
                                        Qwt.QwtPlotPicker.CrossRubberBand,
                                        Qwt.QwtPicker.AlwaysOn,
                                        self.canvas())
        self.picker.setRubberBandPen(QtGui.QPen(Qt.Qt.green))
        self.picker.setTrackerPen(QtGui.QPen(Qt.Qt.cyan))
        self.connect(self.picker, QtCore.SIGNAL('selected(const QPolygon&)'), self.selectPlot)
        
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


    def overlay(self):
        return self.__overlay

    def setOverlay(self, value):
        self.__overlay = value

    def clearZoomStack(self):
        """Auto scale and clear the zoom stack
        """
        self.setAxisAutoScale(Qwt.QwtPlot.xBottom)
        self.setAxisAutoScale(Qwt.QwtPlot.yLeft)
        self.replot()
        self.zoomer.setZoomBase()
        
    def eventFilter(self, obj, event):
        if event.type() == Qt.QEvent.MouseButtonPress:
            self.selectPlot(event.pos())
        return Qwt.QwtPlot.eventFilter(self, obj, event)

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
        if self.legend() is None:
            return
        for item in self.itemList():
            widget = self.legend().find(item)
            if isinstance(widget, Qwt.QwtLegendItem) and widget.isChecked():
                editDialog = QtGui.QInputDialog()
                editDialog.setLabelText('Enter new curve label')
                editDialog.setInputMode(QtGui.QInputDialog.TextInput)
                editDialog.setTextValue(widget.text().text())
                if editDialog.exec_() == QtGui.QDialog.Accepted:
                    widget.setText(Qwt.QwtText(editDialog.textValue()))
                    print 'Current title', item.title().text()
                    item.setTitle(Qwt.QwtText(editDialog.textValue()))
                    widget.setChecked(False)

    def reconfigureSelectedCurves(self, pen, symbol, style, attribute):
        """Reconfigure the selected curves to use pen for line and
        symbol for marking the data points."""
        print 'Reconfiguring slected plots'
        if self.legend() is None:
            return
        for item in self.itemList():
            widget = self.legend().find(item)
            if isinstance(widget, Qwt.QwtLegendItem) and widget.isChecked():
                item.setPen(pen)
                item.setSymbol(symbol)
                item.setStyle(style)
                item.setCurveAttribute(attribute)
        self.replot()
        
    def toggleSelectedCurves(self):
        if self.legend() is None:
            return
        for item in self.itemList():
            widget = self.legend().find(item)
            if isinstance(widget, Qwt.QwtLegendItem) and widget.isChecked():
                item.setVisible(not item.isVisible())
        self.replot()

    def getSelectedCurves(self):
        ret = []
        for item in self.itemList():
            widget = self.legend().find(item)
            if isinstance(widget, Qwt.QwtLegendItem) and widget.isChecked():
                ret.append(item)
        return ret

    def showAllCurves(self):
        for item in self.itemList():
            if isinstance(item, Qwt.QwtPlotCurve):
                print item
                item.setVisible(True)
        self.replot()

    def setLineStyleSelectedCurves(self, style=Qwt.QwtPlotCurve.NoCurve):        
        if self.legend() is None:
            return
        for item in self.itemList():
            widget = self.legend().find(item)
            if isinstance(widget, Qwt.QwtLegendItem) and widget.isChecked():
                item.setStyle(style)
        self.replot()

    def fitSelectedCurves(self):
        for item in self.itemList():
            widget = self.legend().find(item)
            if isinstance(widget, Qwt.QwtLegendItem) and widget.isChecked():
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

    def setLogLogScale(self, x_range, y_range):
        self.setAxisScaleEngine(self.xBottom, Qwt.QwtLog10ScaleEngine())
        if x_range is not None:
            self.setAxisScale(self.xBottom, x_range[0], x_range[1])
        self.setAxisScaleEngine(self.yLeft, Qwt.QwtLog10ScaleEngine())
        if y_range is not None:
            self.setAxisScale(self.yLeft, y_range[0], y_range[1])
        self.replot()
        self.zoomer.setZoomBase()

    def savePlotImage(self, filename):
        pixmap = QtGui.QPixmap(1024, 768)
        pixmap.fill(Qt.Qt.white)
        prnfilter = Qwt.QwtPlotPrintFilter()
        options = prnfilter.PrintAll
        prnfilter.setOptions(options)
        self.print_(pixmap, prnfilter)
        pixmap.save(filename)
                
    def addPlotCurveList(self, pathlist, datalist, curvenames=None, simtime=1.0, colorlist=None, mode='curve'):
        """mode is either curve or raster. just for the defaults for
        continuous/spiketrain data.  will give tools for finer
        manipulations."""
        if len(datalist) != len(pathlist):
            raise Exception('datalist and pathlist must have same length.')
        if curvenames is None:
            curvenames = pathlist
        for ii in range(len(datalist)):
            data = datalist[ii]
            path = pathlist[ii]
            curvename = curvenames[ii]

            if colorlist is not None:
                color = colorlist[ii % len(colorlist)]
            else:
                color = self.nextColor()
            
            curves = self.path_curve_dict[path]
            if curves and not self.overlay():
                curve = curves[0]
            else:
                if curves:
                    curvename = '%s#%d' % (curvename, len(curves))
                curve = Qwt.QwtPlotCurve(curvename)
                self.path_curve_dict[path].append(curve)
                curve.attach(self)
                self.curve_path_dict[curve] = path
            pen = Qt.QPen(color, 1)
            curve.setPen(pen)
            curve.setTitle(curvename)
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

    def getDataPathsForSelectedCurves(self):
        """Get the HDF5 paths for the selected curves"""
        ret = []
        for item in self.itemList():
            widget = self.legend().find(item)
            if isinstance(widget, Qwt.QwtLegendItem) and widget.isChecked():
                ret.append(self.curve_path_dict[item])
        return ret

    
    def vShiftSelectedPlots(self, shift):
        for item in self.itemList():
            widget = self.legend().find(item)
            if isinstance(widget, Qwt.QwtLegendItem) and widget.isChecked():
                data = item.data()
                ydata = numpy.array(data.yData()) + shift
                item.setData(numpy.array(data.xData()), ydata)
                widget.setChecked(False)
        self.replot()
        self.clearZoomStack()

    def vScaleSelectedPlots(self, scale):
        for item in self.itemList():
            widget = self.legend().find(item)
            if isinstance(widget, Qwt.QwtLegendItem) and widget.isChecked():
                data = item.data()
                ydata = numpy.array(data.yData()) * scale
                item.setData(numpy.array(data.xData()), ydata)
                widget.setChecked(False)
        self.replot()
        self.clearZoomStack()
        

    def updatePlots(self, curve_list, data_list):
        for curve, data in zip(curve_list, data_list):
            curve.setData(data[0], data[1])
        self.replot()
        self.clearZoomStack()

    def selectPlot(self, point):
        dist = 10
        selected = None
        closest = -1
        for item in self.itemList():
            if isinstance(item, Qwt.QwtPlotCurve):
                p, d = item.closestPoint(Qt.QPoint(point.x(), point.y()))
                if p > -1 and d < dist:
                    dist = d
                    closest = p
                    selected = item        
        if (selected is not None):
            widget = self.legend().find(selected)
            if isinstance(widget, Qwt.QwtLegendItem):
                widget.setChecked(True)
                self.emit(QtCore.SIGNAL('curveSelected'), widget.text().text())

    def deselectAllCurves(self):
        for item in self.legend().legendItems():
            item.setChecked(False)

    def makeSpectrogram(self, datalist):
        """Display an array of time series data as spectrogram"""
        data = SpectrogramData(datalist)
        spectrogram = Qwt.QwtPlotSpectrogram()
        spectrogram.setData(data)
        spectrogram.attach(self)
        self.clearZoomStack()
            
# 
# plotwidget.py ends here

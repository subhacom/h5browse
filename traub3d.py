# traub3d.py --- 
# 
# Filename: traub3d.py
# Description: 
# Author: 
# Maintainer: 
# Created: Sun Mar 30 15:57:59 2014 (+0530)
# Version: 
# Last-Updated: 
#           By: 
#     Update #: 0
# URL: 
# Keywords: 
# Compatibility: 
# 
# 

# Commentary: 
# 
# Use of vtkLookupTable from
# http://www.vtk.org/Wiki/VTK/Examples/Python/MeshLabelImageColor
# 
# Animation of chart: http://www.vtk.org/pipermail/vtkusers/2012-January/072004.html

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

"""This is another attempt at getting a pretty movie out of traub et
al simulation.

- Subhasis. Sun Mar 30 15:58:42 IST 2014

"""
import sys
import csv
from collections import defaultdict
import numpy as np
from traubdata import TraubData
# import matplotlib.pyplot as plt
# from mpl_toolkits.mplot3d import Axes3D
# import matplotlib as mpl
import vtk
from vtk.util import numpy_support as vtknp
import itertools


# These are the default cellposition and data files
posfile = '/home/subha/src/dataviz/cellpos_const_dia.csv'
datafile = '/data/subha/rsync_ghevar_cortical_data_clone/2012_05_22/data_20120522_152734_10973.h5'

# This uses:
# hue, saturation, value (hsv) colorspec to get well separated colours. 
# ((hue_min, hue_max), (saturation_min, saturation_max), (value_mean, value_max), (alpha_min, alpha_max))
cmap = {'SupPyrRS': ((0.0,0.0), (1, 0.0), (1.0, 1.0), (0.7, 0.7)),
        'SupPyrFRB': ((0.15,0.15), (1,0.0), (1.0, 1.0), (0.7, 0.7)),
        'SupLTS': ((0.25,0.25), (1, 0.0), (1.0, 1.0), (0.7, 0.7)),
        'SupAxoaxonic': ((0.35,0.35), (1, 0.0), (0.5, 1.0), (0.7, 0.7)),
        'SupBasket': ((0.45,0.45), (1, 0.0), (1.0, 1.0), (0.7, 0.7)),
        'SpinyStellate': ((0.9,0.9), (1, 0.0), (1.0, 1.0), (0.7, 0.7)),
        'TuftedIB': ((0.0,0.0), (1, 0.0), (1.0, 1.0), (0.7, 0.7)),
        'TuftedRS': ((0.15,0.15), (1, 0.0), (1.0, 1.0), (0.7, 0.7)),
        'NontuftedRS': ((0.8,0.8), (1, 0.0), (1.0, 1.0), (0.7, 0.7)),
        'DeepBasket': ((0.45,0.45), (1, 0.0), (1.0, 1.0), (0.7, 0.7)),
        'DeepAxoaxonic': ((0.35,0.35), (1, 0.0), (1.0, 1.0), (0.7, 0.7)),
        'DeepLTS': ((0.25,0.25), (1, 0.0), (1.0, 1.0), (0.7, 0.7)),
        'TCR': ((0,0), (1, 0.0), (1.0, 1.0), (0.7, 0.7)),
        'nRT': ((0.5,0.5), (1, 0.0), (1.0, 1.0), (0.7, 0.7)),
}

celltypes = ['SupPyrRS',
             'SupPyrFRB',
             'SupLTS',
             'SupAxoaxonic',
             'SupBasket',
             'SpinyStellate',
             'TuftedIB',
             'TuftedRS',
             'NontuftedRS',
             'DeepBasket',
             'DeepAxoaxonic',
             'DeepLTS',
             'TCR',
             'nRT',]


def read_posdata(filename):
    """Read position data from file"""
    pos = {}
    with open(filename, 'r') as filehandle:
        reader = csv.DictReader(filehandle, fieldnames=['cellclass', 'depth', 'start', 'end', 'dia', 'layer', 'isInTraub'], delimiter=',', quotechar='"')
        reader.next() #Skip the header row
        for row in reader:
            print row
            pos[row['cellclass']] = row
    return pos

def generate_cell_positions(data, cellposfile):
    """Generate positions for cells of each type and return a dict
    mapping celltype to a 3-tuple (x, y, z) where x, y and z are
    arrays representing the respective coordinates of the cells of
    that type.

    """
    cellpos = {}
    celltype_pos = read_posdata(cellposfile)
    for celltype, count in data.cellcounts._asdict().items():
        if count == 0:
            continue
        start = float(celltype_pos[celltype]['start'])
        end = float(celltype_pos[celltype]['end'])
        rad = float(celltype_pos[celltype]['dia'])/2.0
        print celltype, start, end
        zpos = -np.random.uniform(low=start, high=end, size=count)
        rpos = rad * np.sqrt(np.random.uniform(low=0, high=1, size=count))
        theta = np.random.uniform(low=0, high=2*np.pi, size=count)
        xpos = rpos * np.cos(theta)
        ypos = rpos * np.sin(theta)
        # pos = np.c_[xpos, ypos, zpos)
        cellpos[celltype] = (xpos, ypos, zpos)
    return cellpos


def get_display_data(datafile, cellposfile):
    data = TraubData(datafile)
    spiketimes = data.spikes
    vm = dict([(cell, data.fdata['/Vm'][cell][:]) for cell in data.fdata['/Vm' ]])
    pos = generate_cell_positions(data, cellposfile)
    return {
        'spike': spiketimes,
        'pos': pos,
        'vm': vm,
        'data': data}

import threading
import time

t = 0.0

class Animator():
    def __init__(self, lock, moviewriter=None):
        self.lock = lock
        self.moviewriter = moviewriter

    def animate(self, obj=None, event=None):
        time.sleep(0.003)
        self.lock.acquire()
        obj.Render()
        if self.moviewriter is not None:
            self.moviewriter.Write()
        self.lock.release()
    
    def __del__(self):
        if self.moviewriter is not None:
            self.moviewriter.End()

class UpdateThread(threading.Thread):
    """For updating the visualization data"""
    def __init__(self, threadID, threadLock, display_data, polydata_dict, tstart=1.0, tend=None, vmdata_dict=None, vmplot_dict=None):
        self.threadLock = threadLock
        self.threadId = threadID
        self.display_data = display_data
        self.polydata_dict = polydata_dict
        if tend is None:
            tend = display_data['data'].simtime
        self.times = np.arange(tstart, tend, display_data['data'].plotdt)
        self.it = xrange(len(self.times)).__iter__()
        self.vmdata_dict = vmdata_dict
        self.vmplot_dict = vmplot_dict
        self.spikewindow = 5e-3 # Keep effect of spikes in this window
        threading.Thread.__init__(self)        

    def run(self):
        global update_on, t
        while update_on:
            time.sleep(0.001)
            self.threadLock.acquire()
            # print 'Position:', self.actor.GetPosition()
            ii = self.it.next()
            t = self.times[ii]        
            if hasattr(self, 'txtActor'):
                self.txtActor.SetInput('%.6f' % (t))
            for celltype, pos in self.display_data['pos'].items():            
                values = np.zeros(len(pos[0]), order='C')
                for jj in range(len(pos[0])):
                    spikes = self.display_data['spike']['%s_%d' % (celltype, jj)]
                    # Get all the spikes in last 5 ms
                    st = spikes[np.flatnonzero((spikes < t) & (spikes > t - self.spikewindow))]
                    values[jj] = sum(np.exp(st - t))                  
                # print celltype, values
                self.polydata_dict[celltype].GetPointData().SetScalars(vtknp.numpy_to_vtk(values))
            # We display data from 100 ms before present time till 100 ms after present time
            tback = t - thalf
            idxback = int(tback / self.display_data['data'].plotdt)
            print 'Past time:', tback, 'index:', idxback
            # NOTE: no correction for the cycle
            for celltype in celltypes:
                if not self.vmdata_dict:
                    break
                for cellname, vmdata in self.vmdata_dict.items():
                    if not cellname.startswith(celltype):
                        continue
                    for jj in range(vmdata.GetNumberOfRows()):
                        tj = tback + jj * self.display_data['data'].plotdt
                        vj = self.display_data['vm'][cellname][jj + idxback]
                        vmdata.SetValue(jj, 0, tj)
                        vmdata.SetValue(jj, 1, vj)
                    print cellname, vmdata.GetValue(jj, 0), vmdata.GetValue(jj, 1), vmdata.GetNumberOfRows()
                    vmdata.Modified()
            self.threadLock.release()
                

update_on = True
thalf = 100e-3

def display_3d(datafile, cellposfile, moviefile=None):
    global update_on
    display_data = get_display_data(datafile, cellposfile)
    renderer = vtk.vtkRenderer()
    renwin = vtk.vtkRenderWindow()
    renwin.StereoCapableWindowOn()
    # renwin.StereoRenderOn()
    # renwin.SetStereoTypeToCrystalEyes()
    # renwin.SetStereoTypeToAnaglyph()
    renwin.AddRenderer(renderer)
    renwin.SetSize(1280, 900)
    scalarbarX = 0.01
    scalarbarY = 0.95
    tstart = 1.0
    tend = 2.0
    polydata_dict = {}
    vmplot_dict = {}
    vmdata_dict = {}
    source_dict = {}
    glyph_dict = {}
    mapper_dict = {}
    actor_dict = {}
    points_dict = {}
    pos_dict = {}
    color_xfn = {}
    scalarbarY_dict = {}
    # 2D plot stuff was figured out from:
    # https://github.com/Kitware/VTK/blob/master/Charts/Core/Testing/Cxx/TestChartsOn3D.cxx
    plot_scene = vtk.vtkContextScene()
    plot_actor = vtk.vtkContextActor()
    plot_actor.SetScene(plot_scene)
    plot_scene.SetRenderer(renderer)
    renderer.AddActor(plot_actor)
    time = vtk.vtkFloatArray()
    time.SetName('time')
    for celltype in celltypes:
        try:
            pos = display_data['pos'][celltype]
        except KeyError:
            continue
        a = np.array(np.column_stack(pos), copy=True, order='C')
        vtkpos = vtknp.numpy_to_vtk(a, deep=True) # vtk needs column major array
        points = vtk.vtkPoints()
        points.SetData(vtkpos)
        polydata = vtk.vtkPolyData()
        polydata.SetPoints(points)
        polydata_dict[celltype] = polydata
        colortab = vtk.vtkLookupTable()
        colortab.SetHueRange(cmap[celltype][0])
        colortab.SetSaturationRange(cmap[celltype][1])
        colortab.SetValueRange(cmap[celltype][2])
        colortab.Build()
        colorXfun = vtk.vtkColorTransferFunction()
        if celltype == 'SpinyStellate':
            source = vtk.vtkSuperquadricSource()
            source.SetThetaResolution(6)
            source.SetPhiResolution(6)
            source.SetPhiRoundness(5)
            source.SetThetaRoundness(5)
            source.SetScale(5, 5, 7)
        elif celltype.endswith('Basket') or celltype.endswith('Axoaxonic') or celltype.endswith('LTS') or celltype == 'nRT':
            source = vtk.vtkSphereSource()
            source.SetThetaResolution(6)
            source.SetPhiResolution(6)
            source.SetRadius(1)
            # source.SetPhiRoundness(1)
            # source.SetThetaRoundness(1)
            # source.SetScale(3, 3, 3)
        elif celltype == 'TCR':
            source = vtk.vtkSuperquadricSource()
            source.SetThetaResolution(6)
            source.SetPhiResolution(6)
            source.SetPhiRoundness(2)
            source.SetThetaRoundness(0)
            source.SetScale(3, 3, 3)        
        elif ('Pyr' in celltype) or celltype in ('NontuftedRS', 'TuftedIB', 'TuftedRS'):
            source = vtk.vtkConeSource()
            source.SetRadius(2)
            source.SetResolution(20)
            source.SetHeight(3)
            source.SetDirection(0, 0, 1)
        # source.SetThetaResolution(20)
        # source.SetPhiResolution(20)       
        glyph = vtk.vtkGlyph3D()
        glyph.SetSource(source.GetOutput())
        glyph.SetInput(polydata)
        glyph.SetScaleModeToDataScalingOff()
        glyph.SetScaleFactor(10)
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInput(glyph.GetOutput())
        mapper.ImmediateModeRenderingOn()
        mapper.SetLookupTable(colortab)
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)        
        # actor.GetProperty().SetOpacity(0.5)
        scalarBar = vtk.vtkScalarBarActor()
        scalarBar.SetLookupTable(colortab)
        scalarBar.SetTitle(celltype)
        # scalarBar.SetNumberOfLabels(4)
        scalarBar.SetPosition(scalarbarX, scalarbarY)
        scalarBar.SetHeight(0.05)
        scalarBar.SetWidth(0.10)
        scalarBar.SetOrientationToHorizontal()
        scalarBar.GetTitleTextProperty().SetOrientation(90.0)
        renderer.AddActor2D(scalarBar)        
        renderer.AddActor(actor)
        # For each cell type add one cell's Vm
        chart = vtk.vtkChartXY()
        chart.SetAutoSize(False);
        chart.SetSize(vtk.vtkRectf(900.0, (scalarbarY-0.07)*900, 300, 100));
        xaxis = chart.GetAxis(0)
        xaxis.SetRange(-thalf, thalf)
        yaxis = chart.GetAxis(1)
        yaxis.SetRange(-120e-3, 100e-3)    
        plot_scene.AddItem(chart)
        for name, vm in display_data['vm'].items():
            if name.startswith(celltype) and len(display_data['spike'][name]) > 0:
                vm = display_data['vm'][name]
                vmtab = vtk.vtkTable()
                vmdata_dict[name] = vmtab
                vmarray = vtk.vtkFloatArray()
                vmarray.SetName('Vm')
                timearray = vtk.vtkFloatArray()
                timearray.SetName('time')
                vmtab.AddColumn(timearray)
                vmtab.AddColumn(vmarray)
                vmtab.SetNumberOfRows(int(2*thalf/display_data['data'].plotdt))
                
                # for ii in range(vmtab.GetNumberOfRows()):
                #     # print '##', ii
                #     vmtab.SetValue(ii, 0, tstart + ii * display_data['data'].plotdt)
                #     vmtab.SetValue(ii, 1, vm[ii+int(tstart/display_data['data'].plotdt)])
                plot = chart.AddPlot(vtk.vtkChart.LINE)
                # print 'Here'
                plot.SetInput(vmtab, 0, 1)
                # print '** Here'
                # plot.SetInputArray(0, 'time')
                # plot.SetInputArray(1, 'Vm')
                color = [255, 255, 255]
                colortab.GetColor(0, color)
                plot.SetColor(*color)
                vmplot_dict[name] = plot
                break
        scalarbarY -= 0.07
    txtActor = vtk.vtkTextActor()
    txtActor.GetTextProperty().SetFontSize(24)
    # txtActor.SetPosition2(100, 10)
    renderer.AddActor2D(txtActor)
    txtActor.SetInput('Starting ...')
    txtActor.GetTextProperty().SetColor(1, 1, 0)
    camera = vtk.vtkCamera()
    camera.SetPosition(0.0, 500.0, -1200.0)
    camera.SetFocalPoint(0, 0, -1200)
    camera.ComputeViewPlaneNormal()
    renderer.SetActiveCamera(camera)
    renderer.ResetCamera()
    # For animation without interaction
    # times = np.arange(1.0, display_data['data'].simtime, display_data['data'].plotdt)
    # it = itertools.cycle(range(len(times)))
    # for ii in it:
    #     t = times[ii]        
    #     for celltype, pos in display_data['pos'].items():
    #         values = np.zeros(len(pos[0]), order='C')
    #         for jj in range(len(pos[0])):
    #             spikes = display_data['spike']['%s_%d' % (celltype, jj)]                
    #             if np.any((spikes < t) & (spikes > t - display_data['data'].plotdt)):
    #                 values[jj] = 1.0
    #                 print t, celltype, jj
    #         polydata_dict[celltype].GetPointData().SetScalars(vtknp.numpy_to_vtk(values))
    #         print celltype, values
    #     renwin.Render()
    # non-interactive animation tille here
    mwriter = None
    if moviefile is not None:
        mwriter = vtk.vtkFFMPEGWriter()
        mwriter.SetQuality(2)
        mwriter.SetFileName(moviefile)
        # mwriter.SetRate(30)
        w2img = vtk.vtkWindowToImageFilter()
        w2img.SetInput(renwin)        
        mwriter.SetInputConnection(w2img.GetOutputPort())
        mwriter.SetQuality(2)
        mwriter.SetRate(30)
    update_on = True
    threadLock = threading.Lock()
    updateThread = UpdateThread(0, threadLock, display_data, polydata_dict, tstart=tstart, tend=tend, vmdata_dict=vmdata_dict, vmplot_dict=vmplot_dict)
    updateThread.start()
    # For timer callback based animation
    # callback = TimerCallback(display_data, polydata_dict, tstart=tstart, tend=tend, vmdata_dict=vmdata_dict, vmplot_dict=vmplot_dict, moviewriter=mwriter)
    callback = Animator(threadLock, moviewriter=mwriter)
    callback.actor = actor
    updateThread.txtActor = txtActor
    renwin.SetMultiSamples(0)
    interactor = vtk.vtkRenderWindowInteractor()
    interactor.SetRenderWindow(renwin)
    interactor.Initialize()
    interactor.AddObserver('TimerEvent', callback.animate)
    timerId = interactor.CreateRepeatingTimer(1)
    # timer callback till here
    # start the interaction and timer
    if mwriter is not None:
        mwriter.Start()
    interactor.Start()
    update_on = False
    interactor.DestroyTimer(timerId)
    updateThread.join()
    
if __name__ == '__main__':
    args = sys.argv
    animate = True
    movie = False
    filename = 'traub_animated.avi'
    print 'Args', args, len(args)
    if len(args) >= 3:
        posfile = args[1]
        datafile = args[2]
        if len(args) > 3:
            animate = True
        if len(args) > 4:
            movie = True
            filename = args[4]
    print 'Visualizing: positions from %s and data from %s' % (posfile, datafile)
    display_3d(datafile, posfile)
# 
# traub3d.py ends here

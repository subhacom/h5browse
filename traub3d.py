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
posfile = '/home/subha/src/dataviz/cellpos.csv'
datafile = '/data/subha/rsync_ghevar_cortical_data_clone/2012_05_22/data_20120522_152734_10973.h5'

# This uses:
# hue, saturation, value (hsv) colorspec to get well separated colours. 
# ((hue_min, hue_max), (saturation_min, saturation_max), (value_mean, value_max))
cmap = {'SupPyrRS': ((0.0,0.0), (1, 0.0), (1.0, 1.0), (0.7, 0.7)),
        'SupPyrFRB': ((0.1,0.1), (1,0.0), (1.0, 1.0), (0.7, 0.7)),
        'SupLTS': ((0.25,0.25), (1, 0.0), (1.0, 1.0), (0.7, 0.7)),
        'SupAxoaxonic': ((0.35,0.35), (1, 0.0), (1.0, 1.0), (0.7, 0.7)),
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
    pos = generate_cell_positions(data, cellposfile)
    return {
            'spike': spiketimes,
            'pos': pos,
            'data': data}

class TimerCallback():
    def __init__(self, display_data, polydata_dict, moviewriter=None):
        self.display_data = display_data
        self.polydata_dict = polydata_dict
        self.times = np.arange(1.0, display_data['data'].simtime, display_data['data'].plotdt)
        self.it = itertools.cycle(range(len(self.times)))
        self.moviewriter = moviewriter
        self.spikewindow = 5e-3 # Keep effect of spikes in this window

    def execute(self, obj, event):
        print self.actor.GetPosition()
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
        obj.Render()
        if self.moviewriter is not None:
            self.moviewriter.Write()

    def __del__(self):
        if self.moviewriter is not None:
            self.moviewriter.End()
                

def display_3d(datafile, cellposfile, moviefile=None):
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

    polydata_dict = {}
    source_dict = {}
    glyph_dict = {}
    mapper_dict = {}
    actor_dict = {}
    points_dict = {}
    pos_dict = {}
    color_xfn = {}
    # cmap_matrix = np.loadtxt('autumn.cmp')
    # values = np.linspace(0, 1, len(cmap_matrix))
    # for ii in range(len(cmap_matrix)):                
    #     colorXfun.AddRGBPoint(values[ii], cmap_matrix[ii][0], cmap_matrix[ii][1], cmap_matrix[ii][2])
    scalarbarX = 0.01
    scalarbarY = 0.95
    
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
            source.SetScale(5, 5, 5)
        elif celltype.endswith('Basket') or celltype.endswith('Axoaxonic') or celltype.endswith('LTS') or celltype == 'nRT':
            source = vtk.vtkSphereSource()
            source.SetThetaResolution(6)
            source.SetPhiResolution(6)
            source.SetRadius(2)
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
            source.SetRadius(1)
            source.SetResolution(20)
            source.SetHeight(2)
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
        scalarbarY -= 0.07
        scalarBar.SetHeight(0.05)
        scalarBar.SetWidth(0.30)
        scalarBar.SetOrientationToHorizontal()
        scalarBar.GetTitleTextProperty().SetOrientation(90.0)
        renderer.AddActor2D(scalarBar)        
        renderer.AddActor(actor)
    # txtActor = vtk.vtkTextActor()
    # txtActor.GetTextProperty().SetFontSize(24)
    # # txtActor.SetPosition2(100, 10)
    # renderer.AddActor2D(txtActor)
    # txtActor.SetInput('Starting ...')
    # txtActor.GetTextProperty().SetColor(1, 1, 0)
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
    # For timer callback based animation
    callback = TimerCallback(display_data, polydata_dict, mwriter)
    callback.actor = actor
    # callback.txtActor = txtActor
    interactor = vtk.vtkRenderWindowInteractor()
    interactor.SetRenderWindow(renwin)
    interactor.Initialize()
    interactor.AddObserver('TimerEvent', callback.execute)
    timerId = interactor.CreateRepeatingTimer(1)
    # timer callback till here
    # start the interaction and timer
    if mwriter is not None:
        mwriter.Start()
    interactor.Start()
    
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

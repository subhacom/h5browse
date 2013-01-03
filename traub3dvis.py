# traub3dvis.py --- 
# 
# Filename: traub3dvis.py
# Description: 
# Author: 
# Maintainer: 
# Created: Wed Jan  2 20:16:06 2013 (+0530)
# Version: 
# Last-Updated: Thu Jan  3 12:03:40 2013 (+0530)
#           By: subha
#     Update #: 430
# URL: 
# Keywords: 
# Compatibility: 
# 
# 

# Commentary: 
# 
# 3 F visualization for part of Traub model.
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

posfile = '/home/subha/src/dataviz/cellpos_compact.csv'
datafile = '/data/subha/rsync_ghevar_cortical_data_clone/2012_11_05/data_20121105_144428_16400.h5'
markers = {'SupPyrRS': '^',
             'SupPyrFRB': '^',
             'SupLTS': 'o',
             'SupAxoaxonic': 'o',
             'SupBasket': 'o',
             'SpinyStellate': '*',
             'TuftedIB': '^',
             'TuftedRS': '^',
             'NontuftedRS': '^',
             'DeepBasket': 'p',
             'DeepAxoaxonic': 'D',
             'DeepLTS': '8',
             'TCR': 'd',
             'nRT': 'o'
             }

def read_posdata(filename):
    """Read position data from file"""
    pos = {}
    with open(filename, 'r') as filehandle:
        reader = csv.DictReader(filehandle, fieldnames=['cellclass', 'depth', 'start', 'end', 'dia', 'layer', 'isInTraub'], delimiter=',', quotechar='"')
        reader.next() #Skip the header row
        for row in reader:
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
    vm = dict([(cell, np.asarray(data.fdata['/Vm'][cell])) for  cell in data.fdata['Vm']])
    pos = generate_cell_positions(data, cellposfile)
    return {'Vm': vm,
            'spike': spiketimes,
            'pos': pos,
            'data': data}
    
def display_traub_mplot3d(datafile, cellposfile):
    display_data = get_display_data(datafile, cellposfile)
    pos = display_data['pos']
    cm = mpl.cm.jet    
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d') 
    for celltype, pos in pos.items():
        ax.scatter(pos[0], pos[1], pos[2], marker=markers[celltype], edgecolors='none', s=40)
    ax.set_axis_off()
    plt.show()

# sources = {'SupPyrRS': vtk.vtkConeSource,
#              'SupPyrFRB': vtk.vtkConeSource,
#              'SupLTS': vtk.vtkSphereSource,
#              'SupAxoaxonic': vtk.vtkSphereSource,
#              'SupBasket': vtk.vtkSphereSource,
#              'SpinyStellate': '*',
#              'TuftedIB': vtk.vtkConeSource,
#              'TuftedRS': vtk.vtkConeSource,
#              'NontuftedRS': vtk.vtkConeSource,
#              'DeepBasket': vtk.vtkSuperQuadricSource,
#              'DeepAxoaxonic': vtk.vtkSuperQuadricSource,
#              'DeepLTS': vtk.vtkSuperQuadricSource,
#              'TCR': 'd',
#              'nRT': vtk.vtkSphereSource
#              }

class TimerCallback():
    def __init__(self, display_data, polydata_dict):
        self.display_data = display_data
        self.polydata_dict = polydata_dict
        self.times = np.arange(1.0, display_data['data'].simtime, display_data['data'].plotdt)
        self.it = itertools.cycle(range(len(self.times)))

    def execute(self, obj, event):
        print self.actor.GetPosition()
        ii = self.it.next()
        t = self.times[ii]        
        self.txtActor.SetInput('%.6f' % (t))
        for celltype, pos in self.display_data['pos'].items():            
            values = np.zeros(len(pos[0]), order='C')
            for jj in range(len(pos[0])):
                spikes = self.display_data['spike']['%s_%d' % (celltype, jj)]                
                if np.any((spikes < t) & (spikes > t - self.display_data['data'].plotdt)):
                    values[jj] = 1.0
            # print celltype, values
            self.polydata_dict[celltype].GetPointData().SetScalars(vtknp.numpy_to_vtk(values))
        obj.Render()
                
        
def display_traub_vtk(datafile, cellposfile):
    display_data = get_display_data(datafile, cellposfile)
    renderer = vtk.vtkRenderer()
    renwin = vtk.vtkRenderWindow()
    renwin.StereoCapableWindowOn()
    renwin.StereoRenderOn()
    renwin.SetStereoTypeToCrystalEyes()
    # renwin.SetStereoTypeToAnaglyph()
    renwin.AddRenderer(renderer)
    renwin.SetSize(1280, 900)
    polydata_dict = {}
    source_dict = {}
    glyph_dict = {}
    mapper_dict = {}
    actor_dict = {}
    points_dict = {}
    pos_dict = {}
    colorXfun = vtk.vtkColorTransferFunction()
    cmap_matrix = np.loadtxt('autumn.cmp')
    values = np.linspace(0, 1, len(cmap_matrix))
    for ii in range(len(cmap_matrix)):                
        colorXfun.AddRGBPoint(values[ii], cmap_matrix[ii][0], cmap_matrix[ii][1], cmap_matrix[ii][2])
    for celltype, pos in display_data['pos'].items():
        a = np.array(np.column_stack(pos), copy=True, order='C')
        vtkpos = vtknp.numpy_to_vtk(a, deep=True) # vtk needs column major array
        points = vtk.vtkPoints()
        points.SetData(vtkpos)
        polydata = vtk.vtkPolyData()
        polydata.SetPoints(points)
        polydata_dict[celltype] = polydata
        if celltype == 'SpinyStellate':
            source = vtk.vtkSuperquadricSource()
            source.SetThetaResolution(6)
            source.SetPhiResolution(6)
            source.SetPhiRoundness(5)
            source.SetThetaRoundness(5)
            source.SetScale(5, 5, 5)
        elif celltype == 'DeepBasket':
            source = vtk.vtkSphereSource()
            source.SetThetaResolution(6)
            source.SetPhiResolution(6)
            source.SetRadius(2)
            # source.SetPhiRoundness(1)
            # source.SetThetaRoundness(1)
            # source.SetScale(3, 3, 3)
        elif celltype == 'DeepLTS':
            source = vtk.vtkSuperquadricSource()
            source.SetThetaResolution(6)
            source.SetPhiResolution(6)
            source.SetPhiRoundness(1)
            source.SetThetaRoundness(0.5)
            source.SetScale(3, 3, 3)
        elif celltype == 'TCR':
            source = vtk.vtkSuperquadricSource()
            source.SetThetaResolution(6)
            source.SetPhiResolution(6)
            source.SetPhiRoundness(2)
            source.SetThetaRoundness(0)
            source.SetScale(3, 3, 3)        
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
        mapper.SetLookupTable(colorXfun)
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        # actor.GetProperty().SetOpacity(0.5)
        renderer.AddActor(actor)
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

    # For timer callback based animation
    callback = TimerCallback(display_data, polydata_dict)
    callback.actor = actor
    callback.txtActor = txtActor
    interactor = vtk.vtkRenderWindowInteractor()
    interactor.SetRenderWindow(renwin)
    interactor.Initialize()
    interactor.AddObserver('TimerEvent', callback.execute)
    timerId = interactor.CreateRepeatingTimer(1) 
    # timer callback till here
   #start the interaction and timer
    interactor.Start()
    

    
if __name__ == '__main__':
    x = display_traub_vtk(datafile, posfile)
# 
# traub3dvis.py ends here

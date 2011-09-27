# animate.py --- 
# 
# Filename: animate.py
# Description: 
# Author: Subhasis Ray
# Maintainer: 
# Created: Tue Sep 27 09:51:03 2011 (+0530)
# Version: 
# Last-Updated: Tue Sep 27 18:35:19 2011 (+0530)
#           By: Subhasis Ray
#     Update #: 421
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

import sys
from collections import defaultdict
import csv
import numpy
import h5py
import vtk
from vtk.util import numpy_support as vtknp

cmp_spring_matrix = numpy.loadtxt('spring.cmp')

cmp_autumn_matrix = numpy.loadtxt('autumn.cmp')

cmp_winter_matrix = numpy.loadtxt('winter.cmp')

cmp_summer_matrix = numpy.loadtxt('summer.cmp')

cmp_bone_matrix = numpy.loadtxt('bone.cmp')

cmp_hot_matrix = numpy.loadtxt('hot.cmp')

cmp_cool_matrix = numpy.loadtxt('cool.cmp')

class TraubDataHandler(object):
    """Read the data from hdf5 file."""
    def __init__(self, datafilename, cellposfilename):
        self.cellclass_list = []
        self.cell_list = []
        self.class_pos_map = {}
        self.pos_list = None
        self.vm = None
        self.datafilename = datafilename
        self.posfilename = cellposfilename
        self.simtime = None
        self.plotdt = None
        self.num_data_points = 0
        self.datafile = None
        self.class_cellcount_map = defaultdict(int)
        self.__read_position_data()
        self.__read_vm_data()
        self.__generate_cell_pos()

    def __read_position_data(self):
        with open(self.posfilename) as filehandle:
            reader = csv.DictReader(filehandle, fieldnames=['cellclass', 'depth', 'start', 'end', 'dia', 'layer', 'isInTraub'], delimiter=',', quotechar='"')
            reader.next() # skip the header
            for row in reader:
                self.class_pos_map[row['cellclass']] = row
                self.cellclass_list.append(row['cellclass'])
                self.class_cellcount_map[row['cellclass']] = 0

    def __read_vm_data(self):
        """Read the Vm arrays from hdf5 data file. The datafile should
        have the arrays under /Vm group and each array should have the
        same name as the cell, which is in the form
        {cellclass}_{index}."""
        datafile = h5py.File(self.datafilename, 'r')
        self.vm_node = datafile['/Vm']
        self.cellcount = len(self.vm_node)
        # Retrieve the length of the first data array
        for cellname, vm_array in self.vm_node.items():
            self.num_data_points = len(vm_array)
            break
        try:
            self.simtime = datafile.attrs['simtime']
            self.plotdt = datafile.attrs['plotdt']
        except KeyError:
            self.simtime = float(self.num_data_points)
            self.plotdt = 1.0
        # Note: vm is column major
        self.vm = numpy.zeros((self.cellcount, self.num_data_points), order='C')
        index = 0
        for cellname, vm_array in self.vm_node.items():
            self.cell_list.append(cellname)
            tmp = cellname.partition('_')
            self.class_cellcount_map[tmp[0]] += 1
            self.vm[index, :] = vm_array[:]
            index += 1
        datafile.close()

    def __generate_cell_pos(self):
        """Create the positions for the cells and save them in pos_list attribute"""
        class_pos = {}
        class_index = defaultdict(int)
        # Generate the positions for cells in each class and save in a map
        for cellclass in self.cellclass_list:
            start_depth = float(self.class_pos_map[cellclass]['start'])
            end_depth = float(self.class_pos_map[cellclass]['end'])
            radius = float(self.class_pos_map[cellclass]['dia'])/2.0
            size = self.class_cellcount_map[cellclass]
            zpos = -numpy.random.uniform(low=start_depth, high=end_depth, size=size)
            rpos = radius * numpy.sqrt(numpy.random.uniform(low=0, high=1.0, size=size))
            theta = numpy.random.uniform(low=0, high=2*numpy.pi, size=size)
            xpos = rpos * numpy.cos(theta)
            ypos = rpos * numpy.sin(theta)
            pos = numpy.column_stack((xpos, ypos, zpos))
            class_pos[cellclass] = pos
            class_index[cellclass] = 0
        # Fill the list of cell positions in the order of cellnames in
        # cell_list.  class_index is index into the next cell to be
        # assigned position in the list of positions for class.
        self.position_array = numpy.zeros((self.cellcount, 3))
        index = 0
        pyramidal_indices = []
        nonpyramidal_indices = []
        for cellname in self.cell_list:
            if cellname.find('Pyr') >= 0:
                pyramidal_indices.append(index)
            else:
                nonpyramidal_indices.append(index)
            cellclass = cellname.partition('_')[0]
            self.position_array[index,:] = class_pos[cellclass][class_index[cellclass],:]
            class_index[cellclass] += 1
            index += 1
        self.pyramidal_indices = numpy.array(pyramidal_indices, dtype='int')
        self.nonpyramidal_indices = numpy.array(nonpyramidal_indices, dtype='int')

class AnimationTimer(object):
    def __init__(self, datahandler, pyramidal_points, nonpyramidal_points):
        self.current_time = 0.0
        self.current_index = 0
        self.datahandler = datahandler
        self.pyramidal_points = pyramidal_points
        self.nonpyramidal_points = nonpyramidal_points
        
    def update(self, obj, event):
        """Update the colours according to Vm."""
        print 'Updating .....', self.current_index
        vm = self.datahandler.vm[:, self.current_index]
        print vm.shape
        pyramidal_vm = vm[self.datahandler.pyramidal_indices]
        nonpyramidal_vm = vm[self.datahandler.nonpyramidal_indices]
        print pyramidal_vm.shape, nonpyramidal_vm.shape
        print self.pyramidal_points.GetPoints().GetNumberOfPoints(), self.nonpyramidal_points.GetPoints().GetNumberOfPoints()
        print pyramidal_vm, nonpyramidal_vm
        self.pyramidal_points.GetPointData().SetScalars(vtknp.numpy_to_vtk(pyramidal_vm))
        self.nonpyramidal_points.GetPointData().SetScalars(vtknp.numpy_to_vtk(nonpyramidal_vm))
        self.current_time += self.datahandler.plotdt
        self.current_index += 1
        obj.GetRenderWindow().Render()
        if self.current_index >= self.datahandler.num_data_points:
            self.current_index = 0
            self.current_time = 0.0

            
class TraubVmDisplay(object):
    def __init__(self, datafilename, posfilename):
        self.datahandler = TraubDataHandler(datafilename, posfilename)        
        self.glyph_source_map = {}
        self.scalarbar = None
        self.renderer = vtk.vtkRenderer()
        self.renwin = vtk.vtkRenderWindow()
        self.renwin.SetSize(1280, 900)
        self.renwin.AddRenderer(self.renderer)
        self.colorfn = vtk.vtkColorTransferFunction()
        colormap_matrix = numpy.loadtxt('cool.cmp')
        index = 0
        for value in numpy.linspace(-120e-3, 40e-3, len(colormap_matrix)):
            self.colorfn.AddRGBPoint(value, colormap_matrix[index, 0], colormap_matrix[index, 1], colormap_matrix[index, 2])
            index += 1
        pyramidal_pos = self.datahandler.position_array[self.datahandler.pyramidal_indices]
        self.pyramidal_pipeline = self.__create_cells(pyramidal_pos, 'cone')        
        nonpyramidal_pos = self.datahandler.position_array[self.datahandler.nonpyramidal_indices]
        self.nonpyramidal_pipeline = self.__create_cells(nonpyramidal_pos, 'sphere')
        
        # Create colour mapping for Vm values
        self.renderer.AddActor(self.pyramidal_pipeline['actor'])
        self.renderer.AddActor(self.nonpyramidal_pipeline['actor'])
        # Set up color-bar
        scalarbar = vtk.vtkScalarBarActor()
        scalarbar.SetLookupTable(self.colorfn)
        scalarbar.SetPosition(0.95, 0.1)
        scalarbar.SetHeight(0.80)
        scalarbar.SetWidth(0.05)
        scalarbar.SetOrientationToVertical()
        self.renderer.AddActor2D(scalarbar)
        self.camera = vtk.vtkCamera() #self.renderer.GetActiveCamera()
        self.camera.SetPosition(0.0, 500.0, -1200.0)
        self.camera.SetFocalPoint(0, 0, -1200)
        self.camera.ComputeViewPlaneNormal()
        self.renderer.SetActiveCamera(self.camera)
        self.renderer.ResetCamera()
        self.interactor = vtk.vtkRenderWindowInteractor()
        self.interactor.SetRenderWindow(self.renwin)

    def __create_cells(self, position_array, glyphtype):
        """Create the pipeline for cells positioned at position_array
        with glyph of geometry glyphtype"""
        print 'Number if cells of', glyphtype, 'kind:', len(position_array)
        position_array = vtknp.numpy_to_vtk(position_array)        
        points = vtk.vtkPoints()
        points.SetData(position_array)
        polydata = vtk.vtkPolyData()
        polydata.SetPoints(points)
        print glyphtype, polydata.GetPoints().GetNumberOfPoints()
        if glyphtype == 'cone':
            source = vtk.vtkConeSource()
            source.SetRadius(1)
            source.SetResolution(20)
            source.SetHeight(2)
            source.SetDirection(0, 0, 1)
            
        else:
            source = vtk.vtkSphereSource()
            source.SetRadius(1)
            source.SetThetaResolution(20)
            source.SetPhiResolution(20)
        glyph = vtk.vtkGlyph3D()
        glyph.SetSource(source.GetOutput())
        glyph.SetInput(polydata)
        glyph.SetScaleModeToDataScalingOff()
        glyph.SetScaleFactor(10)
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInput(glyph.GetOutput())
        mapper.SetLookupTable(self.colorfn)
        mapper.ImmediateModeRenderingOn()
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetOpacity(0.5)
        
        return {
            'positionSource': polydata,
            'glyphSource': source,
            'glyph': glyph,
            'mapper': mapper,
            'actor': actor
            }

    def display(self):
        self.interactor.Initialize()
        self.timer = AnimationTimer(self.datahandler, self.pyramidal_pipeline['positionSource'], self.nonpyramidal_pipeline['positionSource'])
        self.interactor.AddObserver('TimerEvent', self.timer.update)
        self.timerId = self.interactor.CreateRepeatingTimer(1000)
        self.interactor.Start()

        

        
    
        
            
def main(datafilename, posfilename):
    vis = TraubVmDisplay(datafilename, posfilename)
    vis.display()
    
if __name__ == '__main__':
    posfilename = sys.argv[2]
    datafilename = sys.argv[1]
    main(datafilename, posfilename)
        
        


# 
# animate.py ends here

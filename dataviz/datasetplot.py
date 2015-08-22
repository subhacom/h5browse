# datasetplot.py --- 
# 
# Filename: datasetplot.py
# Description: 
# Author: Subhasis Ray
# Maintainer: 
# Created: Fri Aug 21 17:21:21 2015 (-0400)
# Version: 
# Package-Requires: ()
# Last-Updated: Fri Aug 21 19:28:11 2015 (-0400)
#           By: Subhasis Ray
#     Update #: 38
# URL: 
# Doc URL: 
# Keywords: 
# Compatibility: 
# 
# 

# Commentary: 
# 
# 
# 

# Change Log:
# 
# 
# 
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or (at
# your option) any later version.
# 
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with GNU Emacs.  If not, see <http://www.gnu.org/licenses/>.
# 
# 

# Code:

import pyqtgraph as pg
import numpy as np

"""PlotWidget with some minor modifications for dataviz.

"""
class DatasetPlot(pg.PlotWidget):
    # TODO: multiple dataset in same plotwidget? cannot attach to a
    # specific dataset. Update `name` with something more meaningful. Also, allow option of plo
    def __init__(self, *args):
        pg.PlotWidget.__init__(self, *args)
        self.name = ''

    def plotTimeSeries(self, dataset):
        print(dataset, dataset.shape)
        time = np.arange(len(dataset))
        # try: # This is my data dump sepcific ...
        #     sched = dataset.file['/runconfig/scheduling']
        #     print('sched:', sched)
        #     time = np.arange(len(dataset)) * float(sched['simtime']) / len(dataset)
        # except KeyError:
        #     time = np.arange(len(dataset))
        self.plot(time, dataset)
        self.name = '{}:{}'.format(dataset.file.filename,
                                   dataset.name)


# 
# datasetplot.py ends here

# test_pytablesread.py --- 
# 
# Filename: test_pytablesread.py
# Description: 
# Author: 
# Maintainer: 
# Created: Mon Aug 29 10:00:05 2011 (+0530)
# Version: 
# Last-Updated: Mon Aug 29 11:34:06 2011 (+0530)
#           By: subha
#     Update #: 67
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

import h5py
import tables
import numpy
from datetime import datetime

def test_pytables_reading(filename):
    print 'Opening', filename, 'for reading'
    count = 0
    start = datetime.now()
    h5file = tables.openFile(filename, 'r')
    vmnode = h5file.getNode('/Vm')
    prev = None
    for row in vmnode:        
        data = row.read()
        count += 1
        if prev is not None:
            corr = numpy.correlate(prev, data)
        prev = data
    end = datetime.now()
    dt = end - start
    print 'pytables: Time to read %d arrays: %g' % (count, dt.days * 86400 + dt.seconds + 1e-6 * dt.microseconds)
    h5file.close()


def test_h5py_reading(filename):
    print 'Opening:', filename
    count = 0
    start = datetime.now()
    h5file = h5py.File(filename, 'r')
    vmnode = h5file['/Vm']
    prev = None
    for name in vmnode:
        data = vmnode[name]
        npdata = numpy.zeros(shape=data.shape, dtype=data.dtype)
        npdata[:] = data[:]
        count += 1
        if prev is not None:
            corr = numpy.correlate(prev, npdata)
        prev = npdata
        
    end = datetime.now()
    dt = end - start
    print 'h5py: Time to read %d arrays: %g' % (count, dt.days * 86400 + dt.seconds + dt.microseconds * 1e-6)
    h5file.close()


import sys
if __name__ == '__main__':
    
    test_pytables_reading(sys.argv[1])
    test_h5py_reading(sys.argv[1])

# 
# test_pytablesread.py ends here

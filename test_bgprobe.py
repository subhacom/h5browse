# test_bgprobe.py --- 
# 
# Filename: test_bgprobe.py
# Description: 
# Author: 
# Maintainer: 
# Created: Sun Jun 17 14:21:31 2012 (+0530)
# Version: 
# Last-Updated: Mon Jun 18 11:44:34 2012 (+0530)
#           By: subha
#     Update #: 21
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

import unittest
from bgprobe import *

class TestBgProbe(unittest.TestCase):
    def setUp(self):
        print 'setUp'
        self.filehandle = h5.File('/data/subha/rsync_ghevar_cortical_data_clone/2012_06_17/network_20120617_141731_30134.h5.new', 'r')
    
    def tearDown(self):
        print 'tearDown'
        self.filehandle.close()

    def testProbedCells(self):
        probed_cells = get_probed_cells(self.filehandle)
        print 'Cells connected to probe-stimulated cells'
        print probed_cells
        self.assertEqual(len(probed_cells), 38)

if __name__ == '__main__':
    unittest.main()

# 
# test_bgprobe.py ends here

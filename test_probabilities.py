# test_probabilities.py --- 
# 
# Filename: test_probabilities.py
# Description: 
# Author: 
# Maintainer: 
# Created: Thu Mar 22 15:05:41 2012 (+0530)
# Version: 
# Last-Updated: Thu Mar 22 22:22:32 2012 (+0530)
#           By: subha
#     Update #: 7
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

import unittest

class TestSpikeCondProb(unittest.TestCase):
    def setUp(self):
        self.datafilepath = 'test_data/data.h5'
        self.netfilepath = 'test_data/network.h5'
        self.test_object = SpikeCondProb(self.datafilepath, self.netfilepath)

    def test_calc_spike_prob_all_connected(self):
        spike_prob = self.test_object.calc_spike_prob_all_connected(10e-3, 10e-3)
        self.assertAlmostEqual(spike_prob['TCR_2-SupPyrRS_4'], 0.5)




# 
# test_probabilities.py ends here

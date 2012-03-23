# test_probabilities.py --- 
# 
# Filename: test_probabilities.py
# Description: 
# Author: 
# Maintainer: 
# Created: Thu Mar 22 15:05:41 2012 (+0530)
# Version: 
# Last-Updated: Fri Mar 23 11:20:58 2012 (+0530)
#           By: subha
#     Update #: 23
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
from probabilities import SpikeCondProb

class TestSpikeCondProb(unittest.TestCase):
    def setUp(self):
        self.datafilepath = 'test_data/data.h5'
        self.netfilepath = 'test_data/network.h5'
        self.test_object = SpikeCondProb(self.datafilepath, self.netfilepath)

    def test_calc_spike_prob(self):
        spike_prob = self.test_object.calc_spike_prob('TCR_0', 'SupPyrRS_1', 10e-3, 10e-3)
        self.assertAlmostEqual(spike_prob, 0.5)

    def test_calc_spike_prob_all_connected(self):
        spike_prob = self.test_object.calc_spike_prob_all_connected(10e-3, 10e-3)
        self.assertAlmostEqual(spike_prob['TCR_0-SupPyrRS_1'], 0.5)

    def test_calc_spike_prob_all_unconnected(self):
        spike_prob = self.test_object.calc_spike_prob_all_unconnected(10e-3, 10e-3)
        self.assertAlmostEqual(spike_prob['TCR_0-SupPyrRS_0'], 0.2)
        
    def test_calc_prespike_prob_excitatory_connected(self):
        # Only 5 entries in TCR_0 are within (-15 ms, -5 ms) of spike
        # time in SupPyrRS.
        spike_prob = self.test_object.calc_prespike_prob_excitatory_connected(10e-3, 15e-3)
        self.assertAlmostEqual(spike_prob['TCR_0-SupPyrRS_1'], 0.5)


if __name__ == '__main__':
    unittest.main()


# 
# test_probabilities.py ends here

# test_probabilities.py --- 
# 
# Filename: test_probabilities.py
# Description: 
# Author: 
# Maintainer: 
# Created: Thu Mar 22 15:05:41 2012 (+0530)
# Version: 
# Last-Updated: Mon Apr  2 11:04:13 2012 (+0530)
#           By: subha
#     Update #: 66
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
from probabilities import SpikeCondProb, dump_stimulus_linked_probabilities

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

    def test_calc_prespike_prob_excitatory_unconnected(self):
        spike_prob = self.test_object.calc_prespike_prob_excitatory_unconnected(5e-3, 10e-3)
        self.assertAlmostEqual(spike_prob['TCR_1-SupPyrRS_1'], 0.1)

    def test_calc_spike_prob_after_bgstim(self):
        """For this test data.h5 file has a /stimulus/stim_bg with
        stimulus from 1.498 s to 1.5 s, second stimulus from 3.0 to
        3.02 s and a third stimulus from 4.75 s to 4.77 s. Only the
        spike after the first one (at 1.513 s) and the third one will be counted."""
        spike_prob = self.test_object.calc_spike_prob_after_bgstim('SupPyrRS_1', 0.02, 0.01)
        self.assertAlmostEqual(spike_prob, 1.0)

    def test_calc_spike_prob_after_probestim(self):
        spike_prob = self.test_object.calc_spike_prob_after_probestim('SupPyrRS_1', 0.02, 0.01)
        self.assertAlmostEqual(spike_prob, 0.0)

    def test_calc_spikecount_avg_after_bgstim(self):
        """In the spike train there is 1 spiek after 1.51 s and two
        spikes after 4.78 s (4.78575 s and 4.82025 s, which is between
        0.4 s amd 0.5 s after the window start."""
        spike_count_avg = self.test_object.calc_spikecount_avg_after_bgstim('SupPyrRS_1', 0.05, 0.01)
        self.assertAlmostEqual(spike_count_avg, 1.5)

    def test_calc_spikecount_avg_after_probestim(self):
        """In the spike train there is 1 spike at 3.52325 s. The probe
        stimulus ends at 3.0 s. So a delay of 0.5 s with width of 0.05
        s captures this."""
        spike_count_avg = self.test_object.calc_spikecount_avg_after_probestim('SupPyrRS_1', 0.05, 0.5)
        self.assertAlmostEqual(spike_count_avg, 1.0)
        
    def test_dump_stimulus_linked_probabilities(self):        
        filelist = ['/data/subha/rsync_ghevar_cortical_data_clone/2012_03_22/data_20120322_114922_24526.h5']
        dump_stimulus_linked_probabilities(filelist, [0.01, 0.02, 0.03, 0.04, 0.05], [0.0, 0.05])

    def test_get_bg_shortest_path_lengths(self):
        lengths = self.test_object.get_bg_shortest_path_lengths()
        self.assertEqual(len(lengths), 2)

if __name__ == '__main__':
    unittest.main()


# 
# test_probabilities.py ends here

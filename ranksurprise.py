# ranksurprise.py --- 
# 
# Filename: ranksurprise.py
# Description: Rank-surprise (RS) algorithm for burst identification.
# Author: Subhasis Ray
# Maintainer: 
# Created: Thu Dec 13 15:03:05 2012 (+0530)
# Version: 
# Last-Updated: Wed Dec 19 17:31:45 2012 (+0530)
#           By: subha
#     Update #: 418
# URL: 
# Keywords: 
# Compatibility: 
# 
# 

# Commentary: 
# 
# Implements rank surprise algorithm of burst detection/identification
# in a spike train.
#
# Reference: Gourevitch, B. & Eggermont, J. J. A nonparametric
# approach for detection of bursts in spike trains. Journal of
# Neuroscience Methods 160, 349–358 (2007).
# 
# This is a Python adaptation of the matlab code available in the
# supplementary material of the above paper.
# 
# This code requires numpy and scipy modules for python.

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
# When redistributing the code preserve the reference and the credits.

# Code:

from operator import itemgetter
import numpy as np
from scipy.stats import norm
from scipy.stats.mstats import rankdata
# import matplotlib.pyplot as plt

def burst(spiketimes, limit=None, RSalpha=-np.log(0.01)):
    """Detect bursts in spiketimes using Rank-Surprise method by Boris
    Gourevitch and Jos J. Eggermont.

    Reference: Gourevitch, B. & Eggermont, J. J. A nonparametric
    approach for detection of bursts in spike trains. Journal of
    Neuroscience Methods 160, 349-358 (2007).  doi:
    http://dx.doi.org/10.1016/j.jneumeth.2006.09.024

    This is an adaptation of the matlab code available in the
    supplementary material.

    Return a tuple (start, length, RS) where

    start: spike number of burst start for each burst detected

    length: burst length for each burst detected (in spikes)

    RS: `rank surprise` value for each burst detected.
    """
    ##--------------------
    ## General parameters
    # limit for using the real distribution
    q_lim = 30
    # minimum length of a burst in spikes
    l_min = 3
    ##--------------------
    ## General vectors
    # vector (-1)^k
    alternate = np.ones(400)
    alternate[1::2] = -1
    # log factorials
    log_fac = np.cumsum(np.log(np.r_[1:q_lim+1]))
    ##--------------------
    ## Ranks computation
    # compute ISI
    ISI = np.diff(spiketimes)
    N = len(ISI)
    # ISI value not to include in a burst
    if limit is None:
        # percentile 75% by default
        limit = np.percentile(ISI, 75)
    # compute ranks
    R = val2rank(ISI)
    ##---------------------
    ## Find sequences of ISI under `limit`
    ISI_limit = np.diff(np.where(ISI < limit, 1, 0))
    # first time stamp of these intervals
    begin_int = np.nonzero(ISI_limit == 1)[0] + 1
    # manage the first ISI
    if ISI[0] < limit:
        begin_int = np.r_[0, begin_int] # The first ISI is under limit
    # last time stamp of these intervals
    end_int = np.nonzero(ISI_limit == -1)[0]
    # manage the last ISI
    if len(end_int) < len(begin_int):
        end_int = np.r_[end_int, N-1]
    # Length of intervals of interest
    length_int = end_int - begin_int + 1
    ##--------------------
    ## Initializations
    archive_burst_RS = []
    archive_burst_length = []
    archive_burst_start = []
    ##--------------------
    ## Going through the intervals of interest
    for n_j, p_j in zip(begin_int, length_int):
        subseq_RS = []
        # test each set of spikes
        for i in range(p_j - (l_min - 1) + 1):
            # length of burst tested
            for q in range(l_min - 1, p_j - i + 1):
                # statistic
                u = np.sum(R[n_j + i:n_j + i + q])
                u = int(np.floor(u))
                if q < q_lim:
                    # exact discrete distribution
                    k = np.arange((u - q) / N + 1)
                    length_k = len(k)
                    t1 = np.tile(k, (q, 1))
                    t2 = np.tile(np.r_[:q], (length_k, 1)).transpose()
                    l1 = np.log(u - t1 * N - t2)
                    ss = np.sum(l1, axis=0)
                    l2 = log_fac[np.r_[0, k[1:]-1]]
                    l3 = log_fac[q - k - 1]                                  
                    fac1 = np.exp(ss - l2 - l3 - q * np.log(N))
                    fac2 = alternate[:length_k]
                    prob =  np.dot(fac1, fac2)
                else:
                    # Approximate Gaussian distribution
                    prob = normal.cdf((u - q * (N + 1) / 2) / np.sqrt(q * (N**2 - 1) / 12))
                RS = - np.log(prob)
                # archive results for each subsequence [RSstatistic beginning length]
                if RS > RSalpha:
                    subseq_RS.append((np.r_[RS, i, q]))
        # vet results archive to extract most significant bursts                    
        if len(subseq_RS) > 0:
            # sort RS for all subsequences
            subseq_RS = sorted(subseq_RS, key=itemgetter(0), reverse=True)
            while len(subseq_RS) > 0:
                # extract most surprising burst
                current_burst = subseq_RS[0];
                archive_burst_RS.append(current_burst[0])
                archive_burst_length.append(current_burst[2]+1) # number of ISI involved + 1
                archive_burst_start.append(n_j+current_burst[1])
                # remove most surprising burst from the set
                # subseq_RS=subseq_RS(2:end,:);
                # keep only other bursts non-overlapping with this burst 
                subseq_RS = [row for row in subseq_RS[1:] \
                                 if ((row[1] + row[2] - 1) < current_burst[1]) or \
                                 (row[1] > (current_burst[1] + current_burst[2] - 1))]
    # sort bursts by ascending time
    ind_sort = np.argsort(archive_burst_start)
    archive_burst_start = np.take(archive_burst_start, ind_sort).astype(int)
    archive_burst_RS = np.take(archive_burst_RS, ind_sort)
    archive_burst_length = np.take(archive_burst_length, ind_sort).astype(int)
    return (archive_burst_start, archive_burst_length, archive_burst_RS)

##----------------------------
## Utility - Rank computation
def val2rank(values):
    """Convert values to ranks, with mean of ranks for tied values.
    This differs from scipy.stats.mstats.rankdata in using the mean
    rank for all tied ranks."""
    lp = len(values)
    cl = np.argsort(values)
    rk = np.ones(lp)
    rk[cl] = np.r_[0:lp]
    cl2 = np.argsort(-values)
    rk2 = np.ones(lp)
    rk2[cl2] = np.r_[:lp]
    ranks = (lp+1-rk2+rk)/2
    return ranks


# from matplotlib import pyplot as plt

# if __name__ == '__main__':
#     data = np.loadtxt('testspiketrain.txt')
#     plt.plot(data, np.ones(len(data)), 'b+')
#     start, length, RS = burst(data, limit=50e-3, RSalpha=0.1)
#     print start
#     print length
#     print RS
#     plt.plot(data[start], np.ones(len(start)), 'gx')
#     plt.plot(data[start+length-1], np.ones(len(start)), 'rx')
#     plt.show()

# 
# ranksurprise.py ends here

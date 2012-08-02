# categorize.py --- 
# 
# Filename: categorize.py
# Description: 
# Author: 
# Maintainer: 
# Created: Thu Aug  2 14:01:23 2012 (+0530)
# Version: 
# Last-Updated: Thu Aug  2 16:57:05 2012 (+0530)
#           By: subha
#     Update #: 105
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

# categorize the files according bursts

import sqlite3 as sql
import numpy as np
from matplotlib import pyplot as plt
filenames = []

# load data as strings of character
strdata = np.loadtxt('filtered.txt', dtype='str')
conn = sql.connect('ssbursting.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS bursting_ss 
(filename text PRIMARY KEY ASC, simtime real, bginterval real, ppinterval real, spikecount real, cellcount integer, inhibitory integer, tcr integer, stimulated integer, burstlength real, spikesperburst real)''')
c.executemany('''INSERT OR IGNORE INTO bursting_ss VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
	      strdata[1:])
conn.commit()
for colname in strdata[0]:
    print colname, ',',
print
for row in c.execute('''SELECT * FROM bursting_ss WHERE burstlength > 0 ORDER BY filename, simtime'''):
    print row

c.close()

# 
# categorize.py ends here

#!/usr/bin/env python
# analyze_nonbursting.py --- 
# 
# Filename: analyze_nonbursting.py
# Description: 
# Author: 
# Maintainer: 
# Created: Tue Dec  4 16:40:12 2012 (+0530)
# Version: 
# Last-Updated: Tue Dec  4 17:01:54 2012 (+0530)
#           By: subha
#     Update #: 5
# URL: 
# Keywords: 
# Compatibility: 
# 
# 

# Commentary: 
# 
# analyze (possibly using principal components) spiny stellate cells
# that are not bursting.
# 
# The datafiles and the cells that match criterion are in the file
# nonbursting_spinystellates.txt. and
# nonbursting_spinystellate_frac.txt - which has fraction of spiny
# stellate cells that do not burst in each data file.

# Change log:
# 
# 
# 

# Code:

import h5py as h5
import os
print os.getcwd()
from datetime import datetime
from get_files_by_ts import *
import numpy as np
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib import pyplot as plt
from matplotlib._pylab_helpers import Gcf
import random

import analyzer

if __name__ == '__main__':
    pass


# 
# analyze_nonbursting.py ends here

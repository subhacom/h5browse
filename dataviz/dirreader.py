# dirreader.py --- 
# 
# Filename: dirreader.py
# Description: 
# Author: Subhasis Ray
# Maintainer: 
# Created: Fri Aug 28 16:43:08 2015 (-0400)
# Version: 
# Package-Requires: ()
# Last-Updated: Wed Sep  2 19:35:00 2015 (-0400)
#           By: Subhasis Ray
#     Update #: 50
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

"""Read data distributed in a directory structure"""

import os
from PyQt5.QtCore import (Qt, pyqtSignal, QSettings)
from PyQt5.QtWidgets import (QApplication, QWidget)
from pyqtgraph import parametertree as ptree

class DirReader(ptree.ParameterTree):
    def __init__(self, parent=None, showHeader=True):
        super().__init__(parent=parent,
                         showHeader=showHeader)        
        self.settings = QSettings('dataviz', 'dirreader')        
        self.levelRules = []
        self.levelNames = []
        for rule in self.settings.value('levelRules', type=str):
            self.levelRules.append(rule)
        for rule in self.settings.value('levelNames', type=str):
            self.levelNames.append(rule)
        self.dirPath = ptree.Parameter.create(name='Directory',
                                              type='group')
        for ii, (levelName, levelRule) in enumerate(zip(self.levelNames, self.levelRules)):
            self.dirPath.addChild({'name': 'level {}'.format(ii),
                                   'type': 'group',
                                   'children': [
                                       {'name': 'dir',
                                        'type': 'str',
                                        'value': levelName},
                                       {'name': 'rule',
                                        'type': 'str',
                                        'value': levelRule}]})
        self.setParameters(self.dirPath, showTop=True)
            
    def __del__(self):
        self.settings.setValue('levelRules', self.levelRules)
        self.settings.setValue('levelNames', self.levelNames)
        
        
        
import sys

if __name__ == '__main__':
    app = QApplication(sys.argv)
    widget = DirReader()
    print(widget.levelRules)
    widget.levelNames = ['data root', 'date', 'cell']
    widget.levelRules = ['%Y-%m-%d', '*', '*']
    widget.show()
    app.exec()
    sys.exit(0)

# 
# dirreader.py ends here

# dirreader.py --- 
# 
# Filename: dirreader.py
# Description: 
# Author: Subhasis Ray
# Maintainer: 
# Created: Fri Aug 28 16:43:08 2015 (-0400)
# Version: 
# Package-Requires: ()
# Last-Updated: Fri Sep 11 23:39:25 2015 (-0400)
#           By: subha
#     Update #: 154
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
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog)
from PyQt5.QtGui import (QBrush, QColor)
from pyqtgraph import parametertree as ptree

bgBrush = QBrush(QColor('lightsteelblue'))

class PathParams(ptree.parameterTypes.GroupParameter):
    def __init__(self, **opts):
        opts['type'] = 'group'
        opts['addText'] = "Add rule"
        opts['addList'] = ['timestamp', 'regex', 'string']
        super().__init__(**opts)

    def addNew(self, typ):
        val = {'timestamp': 'YYYY-mm-dd HH:MM:SS',
               'regex': '.*',
               'string': '_'}[typ]
        child = self.addChild({
            'name': typ,
            'type': 'str',
            'value': val,
            'removable': True,
            'renamable': True,
        }, autoIncrementName=True)
        for item in child.items:
            item.setBackground(0, bgBrush)
        

class DirReader(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)        
        self.settings = QSettings('dataviz', 'dirreader')        
        self.baseDirLabel = QLabel('Base directory')
        self.baseDirEdit = QLineEdit('.')
        self.baseDirButton = QPushButton('Open')
        self.baseDirButton.clicked.connect(self.selectBaseDir)
        self.baseDirWidget = QWidget()
        layout = QHBoxLayout()
        self.baseDirWidget.setLayout(layout)
        layout.addWidget(self.baseDirLabel)
        layout.addWidget(self.baseDirEdit)
        layout.addWidget(self.baseDirButton)
        self.pathTree = ptree.ParameterTree(showHeader=False)
        self.pathRules = PathParams(name='Path rules')
        self.pathTree.setParameters(self.pathRules, showTop=True)
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self.baseDirWidget)
        self.layout().addWidget(self.pathTree)
            
    def save(self, key='dirPathState'):
        state = self.pathRules.saveState(filter='user')
        self.settings.setValue(key, state)

    def restore(self, key='dirPathState'):
        state = settings.value(key, [])
        if state != []:
            self.pathRules.restoreState(state)

    def selectBaseDir(self):
        baseDir = QFileDialog.getExistingDirectory()
        self.baseDirEdit.setText(baseDir)
        
import sys

if __name__ == '__main__':
    app = QApplication(sys.argv)
    widget = DirReader()
    widget.show()
    app.exec()
    sys.exit(0)

# 
# dirreader.py ends here
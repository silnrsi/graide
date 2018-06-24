#    Copyright 2012, SIL International
#    All rights reserved.
#
#    This library is free software; you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as published
#    by the Free Software Foundation; either version 2.1 of License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#    Lesser General Public License for more details.
#
#    You should also have received a copy of the GNU Lesser General Public
#    License along with this library in the file named "LICENSE".
#    If not, write to the Free Software Foundation, 51 Franklin Street,
#    suite 500, Boston, MA 02110-1335, USA or visit their web page on the 
#    internet at http://www.fsf.org/licenses/lgpl.html.

from qtpy import QtGui
import sys

Layout = None

class BaseLayout(object) :
    buttonSpacing = 1
    buttonMargins = (0, 0, 0, 0)
    runEditHeight = 60
    errorColour = QtGui.QColor(255, 160, 160)           # pink
    warnColour = QtGui.QColor(255, 255, 160)            # yellow
    activePassColour = QtGui.QColor(255, 255, 208)      # light yellow
    semiActivePassColour = QtGui.QColor(255, 240, 215)  # light peach (actually this is used for collisions which are also active passes)
    slotColours = {
        'default' : QtGui.QColor(0, 0, 0, 32),          # gray, semi-transparent
        'input' : QtGui.QColor(255, 255, 0, 32),        # yellow, semi-transparent
        'output' : QtGui.QColor(0, 170, 0, 32),         # green, semi-transparent
        'inAndOut' : QtGui.QColor(100, 160, 0, 32),     # yellow-green, semi-transparent
        'failed' : QtGui.QColor(0, 0, 0, 32),           # gray, semi-transparent
        'exclude' : QtGui.QColor(255, 160, 0, 60),      # orange, semi-transparent
    }
    posdotColour = QtGui.QColor(0, 160, 0, 192)         # green
    posdotShiftColour = QtGui.QColor(0, 0, 192, 192)    # blue
    initHSplitWidth = 300
    initWinSize = (1000, 700)
    noMenuIcons = False

class MacLayout(BaseLayout) :
    noMenuIcons = True

class WinLayout(BaseLayout) :
    pass

layouts = {
    'darwin' : MacLayout,
    'win32' : WinLayout
}

Layout = layouts.get(sys.platform, BaseLayout)


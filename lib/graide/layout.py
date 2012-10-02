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

from PySide import QtGui

class Layout(object) :
    buttonSpacing = 1
    buttonMargins = (0, 0, 0, 0)
    runEditHeight = 60
    errorColour = QtGui.QColor(255, 160, 160)
    warnColour = QtGui.QColor(255, 255, 160)
    activePassColour = QtGui.QColor(255, 255, 208)	# light yellow
    slotColours = {
        'default' : QtGui.QColor(0, 0, 0, 32),    # gray, semi-transparent
        'input' : QtGui.QColor(200, 00, 0, 32),   # pink, semi-transparent
        'output' : QtGui.QColor(0, 200, 0, 32),   # green, semi-transparent
    }
    posdotColour = QtGui.QColor(0, 160, 0, 192)	  # green
    posdotShiftColour = QtGui.QColor(0, 0, 192, 192)  # blue


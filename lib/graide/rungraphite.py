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

from graide.graphite import gr2, grversion
import sys
from ctypes import *
from ctypes.util import find_library

libc = cdll.LoadLibrary(find_library("c"))
if sys.platform == "win32" :
    c = libc._fdopen
else :
    c = libc.fdopen

c.restype = c_void_p
c.argtypes = [c_int, c_char_p]

def strtolong(txt) :
    res = 0
    if txt :
        txt = (txt + "\000\000\000\000")[:4]
    else :
        return 0
    for c in txt :
        res = (res << 8) + ord(c)
    return res

def runGraphite(font, text, debugname, feats = {}, rtl = 0, lang = None, size = 16) :
    (major, minor, debug) = grversion()
    grface = gr2.gr_make_file_face(font, 0)
    lang = strtolong(lang)
    grfeats = gr2.gr_face_featureval_for_lang(grface, lang)
    for f, v in feats.items() :
        id = gr2.gr_str_to_tag(f)
        fref = gr2.gr_face_find_fref(grface, id)
        gr2.gr_fref_set_feature_value(fref, v, grfeats)
    grfont = gr2.gr_make_font(size, grface)
    if major > 1 or minor > 1 :
        gr2.graphite_start_logging(grface, debugname)
    else :
        debugfile = open(debugname, "w+")
        fd = c(debugfile.fileno(), "w+")
        gr2.graphite_start_logging(fd, 0xFF)
    seg = gr2.gr_make_seg(grfont, grface, 0, grfeats, 1, text.encode('utf_8'), len(text), rtl)
    if major > 1 or minor > 1 :
        gr2.graphite_stop_logging(grface)
    else:
        gr2.graphite_stop_logging()
        debugfile.close()


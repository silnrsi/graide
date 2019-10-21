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

import sys
from graphite2 import gr2, grversion

def strtolong(txt) :
    if txt :
#        txt = (txt + b"\000\000\000\000")[:4]
        txt = bytestostr(txt)
    else :
        return 0

    res = 0
    for c in txt :
        res = (res << 8) + ord(c)
    for i in range(len(txt), 4) :
        res = (res << 8)  # zero-pad

    return res


def bytestostr(byteseq):
    if not isinstance(byteseq,str):
        res = byteseq.decode('utf-8')
    else:
        res = byteseq  # already a str

    # Another implementation - which is faster?
#    try: res = byteseq.decode('utf-8')
#    except: res = byteseq

    return res


def runGraphite(fontname, text, debugname, feats = {}, rtl = 0, lang = None, size = 16, expand = 100) :
    #print("runGraphite")

    (major, minor, debug) = grversion()
    grface = gr2.gr_make_file_face(fontname, 0)

    lang = strtolong(lang)
    
    grfeats = gr2.gr_face_featureval_for_lang(grface, lang)
    for f, v in feats.items() :
        if v is None : continue
        id = gr2.gr_str_to_tag(f)
        fref = gr2.gr_face_find_fref(grface, id)
        gr2.gr_fref_set_feature_value(fref, int(v), grfeats)
    grfont = gr2.gr_make_font(size, grface)
    
    if major > 1 or minor > 1 :
        gr2.gr_start_logging(grface, debugname)
    else :
        debugfile = open(debugname, "w+")
        fd = debugfile.fileno()
        gr2.graphite_start_logging(fd, 0xFF)
        
    text_utf8 = text.encode('utf_8')
    seg = gr2.gr_make_seg(grfont, grface, 0, grfeats, 1, text_utf8, len(text), rtl)
    width = gr2.gr_seg_advance_X(seg)
    ###print("width=",width)
    
    if expand != 100 :
        width = width * expand / 100
        width = gr2.gr_seg_justify(seg, gr2.gr_seg_first_slot(seg), grfont, width, 0, 0, 0)
        
    if major > 1 or minor > 1 :
        gr2.gr_stop_logging(grface)
    else:
        gr2.graphite_stop_logging()
        debugfile.close()
        
    return width
# end of runGraphite


def makeFontAndFace(fontname, size) :
    #print("makeFontAndFace", fontname, size)
    grface = gr2.gr_make_file_face(fontname.encode(), 0)
    grfont = gr2.gr_make_font(size, grface)
    return (grface, grfont)
    
# end of makeFontAndFace


def runGraphiteWithFontFace(faceAndFont, text, debugname, feats = {}, rtl = 0, lang = None, size = 16, expand = 100) :
    #print("runGraphiteWithFontFace")

    (grface, grfont) = faceAndFont

    (major, minor, debug) = grversion()
    if major > 1 or minor > 1 :
        gr2.gr_start_logging(grface, debugname.encode())
    else :
        debugfile = open(debugname, "w+")
        #print("open", debugname)
        fd = debugfile.fileno()
        gr2.graphite_start_logging(fd, 0xFF)

    lang = strtolong(lang)
    grfeats = gr2.gr_face_featureval_for_lang(grface, lang)
    for f, v in feats.items() :
        if v is None :
            continue
        fbytes = f.encode() if isinstance(f, str) else f
        tid = gr2.gr_str_to_tag(fbytes) # Python 2.7
        fref = 0
        try:
            fref = gr2.gr_face_find_fref(grface, tid)
        except:
            print("Invalid feature settings")

        gr2.gr_fref_set_feature_value(fref, int(v), grfeats)
       
    if major > 1 or minor > 1 :
        gr2.gr_start_logging(grface, debugname.encode())
    else :
        debugfile = open(debugname, "w+")
        fd = debugfile.fileno()
        gr2.graphite_start_logging(fd, 0xFF)

    ###print "text=",text  ####
    text_utf8 = text.encode('utf_8', errors='surrogatepass')  # don't crash on surrogates, they print as boxes
    ###print "utf8=",text_utf8  ####
    seg = gr2.gr_make_seg(grfont, grface, 0, grfeats, 1, text_utf8, len(text), rtl)
    width = gr2.gr_seg_advance_X(seg)
    ###print("width=", width)
    
    if expand != 100 :
        width = width * expand / 100
        width = gr2.gr_seg_justify(seg, gr2.gr_seg_first_slot(seg), grfont, width, 0, 0, 0)
    
    if major > 1 or minor > 1 :
        gr2.gr_stop_logging(grface)
    else:
        gr2.graphite_stop_logging()
        debugfile.close()
        print("close", debugname)

    return width

# end of runGraphiteWithFontFace

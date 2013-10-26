#    Copyright 2013, SIL International
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

import re
from xml.etree import cElementTree as et
from graide.utils import reportError
from rungraphite import makeFontAndFace


class GlyphPatternMatcher() :
    
    def __init__(self, app) :
        self.app = app
        self.pattern = ""
    
    # Create a reg-exp from the list of glyphs in the pattern JSON.
    def tempCreateRegExp(self, font, json, startI = 0, endI = 3) :
        jsonOutput = json[0]["output"]
        pattern = ""
        tempCnt = 0
        for g in jsonOutput :
            if tempCnt < startI :
                continue
            if g["gid"] == 848 :
                classData = font.classes['cDiacritics']
                pattern += "("
                sep = ""
                for classGlyph in classData.elements :
                   pattern += sep + "_" + str(classGlyph)
                   sep = "|"
                pattern += ")"
            else :    
                pattern += "_" + str(g["gid"])
                
            tempCnt = tempCnt + 1
            if tempCnt >= endI :
                break;
               
        self.pattern = pattern
        print self.pattern
        
    # Search for all matches of the stored pattern in the target file, which is an XML test file.
    def search(self, fontFile, targetFile) :
        
        print "Searching " + targetFile + " for '" + self.pattern + "'..."
        
        cpat = re.compile(self.pattern)  # compiled pattern
        
        matches = {}
        
        # Read and parse the target file.
        try :
            e = et.parse(targetFile)
        except Exception as err :
            reportError("Could not search %s: %s" % (targetFile, str(err)))
            print "could not search " + targetFile ####
            return
            
        faceAndFont = makeFontAndFace(fontFile, 12)

        cnt = 0;
        for g in e.iterfind('testgroup') :
            groupLabel = g.get('label')
            for t in g.iterfind('test') :
                testLabel = t.get('label')
                r = t.get('rtl')
                testRtl = True if r == 'True' else False
                d = t.find('string')
                if d is None : d = t.find('text')
                testString = d.text if d is not None else ""
                
                #print testLabel
                
                jsonOutput = self.app.runGraphiteOverString(fontFile, faceAndFont, testString, 12, testRtl, {}, {}, 100)
                glyphOutput = self._dataFromGlyphs(jsonOutput)
                #print glyphOutput
                match = cpat.match(glyphOutput)
                if match :
                    matches[testLabel] = testString
                    print testLabel + " matched"
                #else :
                #    print testLabel + " did not match"
                
                cnt = cnt + 1
                if cnt > 25 : break;
            # end of for t loop
            
            if cnt > 25 : break;
        # end of for g loop

        #output = self._dataFromGlyphs(jsonTemp)
        #print output
        #cpat = re.compile(self.pattern)
        #result = cpat.match(output)
        #print result
        
    def _singleGlyphPattern(self) :
        return "_[0-9]+"
        
        
    #def _outputData(jsonResult) :
    
    # Generate a data string corresponding to the glyph output
    # that can be matched against the reg-exp.
    def _dataFromGlyphs(self, json) :
        jsonOutput = json[0]["output"]
        result = ""
        for g in jsonOutput :
            result += "_" + str(g["gid"])
        return result
        
    
# end of GlyphPatternMatcher class
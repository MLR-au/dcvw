# Copyright (c) 2013, Deakin University
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without 
#  modification, are permitted provided that the following conditions are met:
#
# - Redistributions of source code must retain the above copyright notice, 
#    this list of conditions and the following disclaimer.
# - Redistributions in binary form must reproduce the above copyright notice, 
#    this list of conditions and the following disclaimer in the documentation 
#    and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" 
#  AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE 
#  IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE 
#  ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE 
#  LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR 
#  CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF 
#  SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS 
#  INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN 
#  CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) 
#  ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE 
#  POSSIBILITY OF SUCH DAMAGE.

from lxml import etree

class elements:
    def __init__(self):
        pass

    def strip_empty_elements(self, doc):
        """Remove empty elements from the document.

        Solr date fields don't like to be empty - hence why this
        method exists. As it turns out, it can't hurt to ditch empty
        elements - less to submit. Hence why it's generic
        
        @params:
        doc: the XML document
        """
        for elem in doc.iter('field'):
            if elem.text is None:
                elem.getparent().remove(elem)


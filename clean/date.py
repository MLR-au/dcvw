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

from datetime import datetime

class date_cleanser:
    def __init__(self):
        # time formats we will try to clean
        self.timeformats = [
            "%Y-%m-%d", # 1976-01-01
            "%Y %m %d", # 1976 01 01
            "%d %B %Y", # 12 January 1997
            "%B %Y",    # February 1998
            "%Y",       # 2004
            "c. %Y",    # c. 2004
            "%Y?",      # 2004?
        ]

        # the list of date fields in use
        #self.date_fields = date_fields

    def clean(self, datevalue):
        """Date data needs to be in Solr date format

        The format for this date field is of the form 1995-12-31T23:59:59Z,

        @params:
        date: the date string we want to standardise
        """
        #  handle whatever it is we find...
        for timeformat in self.timeformats:
            try:
                datevalue = datetime.strptime(datevalue, timeformat)
                datevalue = "%sZ" % str(datevalue).replace(' ', 'T')
                break
            except:
                pass
                # ie try the next format until we succeed, or get to the end of the list

        # here we check that we can read the datevalue using
        #  the expected format. If there wasn't a suitable format in the list,
        #  then here we'll find the original string, it will fail, and a warning
        #  will be issued.
        try:
            checkdate = datetime.strptime(datevalue, "%Y-%m-%dT%H:%M:%SZ")
            return datevalue
        except ValueError:
            #log.warn("Unknown time format: %s" % datevalue)
            return None



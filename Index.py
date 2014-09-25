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

import logging
import requests

# get the logger
log = logging.getLogger(__name__)

# quieten the requests library
requests_log = logging.getLogger("requests")
requests_log.setLevel(logging.ERROR)

class Index:
    """All the required to manage submission to Solr"""
    def __init__(self, solr):
        self.update_url = "%s/%s" % (solr, 'update?')
        log.debug("Solr: %s" % (self.update_url))
        self.headers = { 'Content-type': 'text/xml; charset=utf-8' }

    def commit(self):
        """Commit the pending updates"""
        msg = '<commit expungeDeletes="true"/>'
        log.debug("Commit message: %s" % msg)
        resp = requests.post(self.update_url, msg, headers=self.headers)
        if resp.status_code == 200:
            log.debug("Successfully committed the changes.")
        else:
            log.error("Something went wrong trying to commit the changes.")
            log.error("\n%s" % resp.text)

    def clean(self, match):
        """Delete all documents

        If a site is specified, then only the documents of that site will be purged.
        """
        if match is not None:
            msg = "<delete><query>%s</query></delete>" % match
        else:
            msg = "<delete><query>*:*</query></delete>"
        resp = requests.post(self.update_url, msg, headers=self.headers)

        log.debug("Purge message: %s" % msg)
        if resp.status_code == 200:
            log.debug("Successfully submitted the index delete request.")
        else:
            log.error("Something went wrong trying to submit a request to wipe the index.")
            log.error("\n%s" % resp.text)

    def optimize(self):
        """Optimize the on disk index"""
        msg = '<optimize waitSearcher="false"/>'
        log.debug("Optimize: message: %s" % msg)
        resp = requests.post(self.update_url, msg, headers=self.headers)
        if resp.status_code == 200:
            log.debug("Successfully optimized the index.")
        else:
            log.error("Something went wrong trying to optimize the index.")
            log.error("\n%s" % resp.text)

    def submit(self, doc, document_name):
        """Submit the document for indexing"""
        resp = requests.post(self.update_url, data=doc, headers=self.headers)
        if resp.status_code == 200:
            log.debug("%s successfully submitted for indexing." % document_name)
        else:
            log.error("Submission of %s failed with error %s." % (document_name, resp.status_code))


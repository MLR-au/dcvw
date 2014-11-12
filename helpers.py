
import sys
import logging
import os.path
import shutil
from lxml import etree, html
from clean.empty import elements
from clean.date import date_cleanser
from clean.markup import markup_cleanser
import requests
from datetime import datetime, timedelta


# the names of the fields which could have a date
date_fields = [ 'date_from', 'date_to', 'date_created' ]

# the names of the fields which could have markup
markup_fields = [ 'abstract', 'text', 'locality' ]

def clean_dates(doc):
    """Date data needs to be in Solr date format

    The format for this date field is of the form 1995-12-31T23:59:59Z,

    @params:
    doc: the XML document
    """
    date_elements = [ e for e in doc.iter() if e.get('name') in date_fields ]
    for e in date_elements:
        # have we found an empty or missing date field ?
        if e.text is None:
            continue

        dc = date_cleanser()
        datevalue = dc.clean(e.text)
        e.text = datevalue

def clean_markup(doc):
    """We don't want markup in the content being indexed

    @params:
    doc: the XML document
    """
    markup_elements = [ e for e in doc.iter() if e.get('name') in markup_fields ]
    for e in markup_elements:
        # have we found an empty or missing date field ?
        if e.text is None:
            continue

        e.text = markup_cleanser().clean(e.text)




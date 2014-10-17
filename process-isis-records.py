#!/usr/bin/env python


import argparse
import ConfigParser
from lxml import etree
import os
import os.path
import sys
from fnmatch import fnmatch
from glob import glob
import subprocess
import copy
import shlex
import shutil

# get the logger
import logging
log = logging.getLogger(__name__)

from Index import *
from clean.empty import elements
from helpers import *

class Common:
    def __init__(self):
        # the names of the fields which could have a date
        self.date_fields = [ 'date_from', 'date_to' ]

        # the names of the fields which could have markup
        self.markup_fields = [ 'abstract', 'text' ]

    def add_field(self, doc, field_name, field_value):
        tmp = doc.xpath('/add/doc')[0]

        # add the record and item metadata 
        b = etree.Element('field', name=field_name)
        b.text = field_value.decode('utf-8')
        tmp.append(b)

        add = etree.Element('add')
        add.append(tmp)
        return add

    def transform_record(self, doc, transform):
        #if os.path.basename(doc) == 'CBB100627.xml':
        try:
            log.debug("Reading in XSL transform to process metadata_file: %s" % transform)
            xsl = etree.parse(transform)
            xsl.xinclude()
            xsl = etree.XSLT(xsl)
        except IOError:
            log.error("No such transform: %s" % transform)
            return
        except etree.XSLTParseError:
            log.error("Check the stylesheet; I can't parse it! %s" % transform)
            return

        # read in the document
        try:
            tree = etree.parse(doc)
        except:
            log.error("Couldn't process: %s" % doc)
            log.error(sys.exc_info()[1])
            return

        # transform it!
        log.debug("Transforming: %s" % doc)
        d = xsl(tree)

        # clean the date entries for solr
        clean_dates(d)

        try:
            # clean the fields with markup
            clean_markup(d)
        except ValueError:
            log.error("I think there's something wrong with the transformed result of: %s" % doc[0])

        # strip empty elements - dates in particular cause
        #  solr to barf horribly...
        elements().strip_empty_elements(d)
        
        #log.debug("Metadata\n%s" % etree.tostring(d, pretty_print=True))
        return d

class EAC(Common):
    def __init__(self, eac_input, output_folder, transforms, url_base):
        self.output_folder = output_folder

        self.eac_input = eac_input
        self.eac_transform = os.path.join(transforms, 'eac.xsl')

        self.url_base = url_base

        self.setup()

    def run(self):
        for (dirpath, dirnames, filenames) in os.walk(self.eac_input):
            dirname = os.path.basename(dirpath)
            solr_output = os.path.join(self.output_folder, 'eac', dirname, 'solr')
            #orig_output = os.path.join(self.output_folder, dirname, 'eac/original')

            if not os.path.exists(solr_output):
                os.makedirs(solr_output)

            #if not os.path.exists(orig_output):
            #    os.mkdir(orig_output)

            for f in filenames:
                file_basename = f
                src = os.path.join(dirpath, f)
                log.info("Processing: %s" % src)
                d = self.transform_record(src, self.eac_transform)
                if d is None:
                    continue

                d = self.add_field(d, 'id', "EAC_%s" % file_basename.split('.')[0])
                output_file = os.path.join(solr_output, file_basename)
                f = open(output_file, 'w')
                f.write(etree.tostring(d, pretty_print=True))
                f.close()

                #tgt = os.path.join(orig_output, file_basename)
                #shutil.copyfile(src, tgt)
                #sys.exit()
                    
    def setup(self):
        # walk the path and process the content
        log.info('Setting up the required folder structure')
        output_folder = os.path.join(self.output_folder, 'eac') 
        if not os.path.exists(output_folder):
            log.debug("Creating: %s" % output_folder)
            os.makedirs(output_folder)
 
class MODS(Common):
    def __init__(self, mods_input, output_folder, transforms, url_base):
        self.output_folder = output_folder

        self.mods_input = mods_input
        self.mods_transform = os.path.join(transforms, 'mods.xsl')
        self.url_base = url_base
        log.debug("MODS input: %s" % self.mods_input)
        log.debug("MODS transform: %s" % self.mods_transform)

        self.setup()

    def run(self):
        for (dirpath, dirnames, filenames) in os.walk(self.mods_input):
            dirname = os.path.basename(dirpath)
            solr_output = os.path.join(self.output_folder, 'mods', dirname, 'solr')
            #orig_output = os.path.join(self.output_folder, 'mods/original', dirname)

            if not os.path.exists(solr_output):
                os.makedirs(solr_output)

            #if not os.path.exists(orig_output):
            #    os.mkdir(orig_output)

            for f in filenames: 
                file_basename = f
                src = os.path.join(dirpath, f)
                log.info("Processing: %s" % src)
                d = self.transform_record(src, self.mods_transform)
                if d is None:
                    continue

                d = self.add_field(d, 'id', "EAC_%s" % file_basename.split('.')[0])
                output_file = os.path.join(solr_output, file_basename)
                f = open(output_file, 'w')
                f.write(etree.tostring(d, pretty_print=True))
                f.close()

                #tgt = os.path.join(orig_output, file_basename)
                #shutil.copyfile(src, tgt)
                #sys.exit()

    def setup(self):
        # walk the path and process the content
        log.info('Setting up the required folder structure')
        output_folder = os.path.join(self.output_folder, 'mods') 
        if not os.path.exists(output_folder):
            log.debug("Creating: %s" % output_folder)
            os.makedirs(output_folder)
 
if __name__ == "__main__":
    
    # read and check the options
    parser = argparse.ArgumentParser(description='DCVW ISIS Batch Processor')

    parser.add_argument('--config',   dest='config', required=True, help='The path to the config file.')
    parser.add_argument('--mods',     dest='mods', default=None, help='The location of the MODS records')
    parser.add_argument('--eac',      dest='eac', default=None, help='The location of the EAC records')

    parser.add_argument('--crawl', dest='crawl', action='store_true', default=None,
        help='Only perform the crawl and transform stages.')
    parser.add_argument('--post', dest='post', action='store_true', default=None,
        help='Only perform the post stage (includes index clean).')

    parser.add_argument('--info', dest='info', action='store_true', help='Turn on informational messages')
    parser.add_argument('--debug', dest='debug', action='store_true', help='Turn on full debugging (includes --info)')

    args = parser.parse_args()

   # unless we specify otherwise
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)

    if args.info:
        logging.basicConfig(level=logging.INFO)

    if not (args.debug and args.info):
        # just give us error messages
        logging.basicConfig(level=logging.WARN)


    # ensure with a volume is specified or the MODS / EAC records
    if args.mods is None and args.eac is None and args.crawl is not None:
        log.error("Must specifiy either --mods and --eac")
        sys.exit()

    # get the default configuration
    cfg = ConfigParser.SafeConfigParser()
    cfg.read(args.config)

    output_folder = cfg.get('General', 'output') if (cfg.has_section('General') and cfg.has_option('General', 'output')) else None
    transforms = cfg.get('General', 'transforms') if (cfg.has_section('General') and cfg.has_option('General', 'transforms')) else None
    url_base = cfg.get('General', 'url_base') if (cfg.has_section('General') and cfg.has_option('General', 'url_base')) else None
    solr = cfg.get('General', 'solr') if (cfg.has_section('General') and cfg.has_option('General', 'solr')) else None
 
    if not os.path.exists(output_folder):
        os.mkdir(output_folder)

    if (args.crawl and args.mods) is not None:
        log.debug("Processing: '%s'. Output: '%s'." % (args.mods, output_folder))
        mods = MODS(args.mods, output_folder, transforms, url_base)
        mods.run()

    if (args.crawl and args.eac) is not None:
        log.debug("Processing: '%s'. Output: '%s'." % (args.eac, output_folder))
        eac = EAC(args.eac, output_folder, transforms, url_base)
        eac.run()

    if args.post is not None:
        if args.mods is not None:
            solr_content = args.mods
        if args.eac is not None:
            solr_content = args.eac
        log.info("Posting the data in: %s" % solr_content)
        i = Index(solr)
        i.commit()
        i.optimize()

        # walk the path looking for the solr folder
        for (dirpath, dirnames, filenames) in os.walk(solr_content):
            if os.path.basename(dirpath) == 'solr':
                for f in filenames:
                    solr_doc = os.path.join(dirpath, f)
           
                    doc = etree.parse(solr_doc)
                    i.submit(etree.tostring(doc), solr_doc)
                i.commit()
                i.optimize()


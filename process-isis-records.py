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

class Common:
    def __init__(self):
        pass

    def add_field(self, doc, field_name, field_value):
        tmp = doc.xpath('/add/doc')[0]

        # add the record and item metadata 
        b = etree.Element('field', name=field_name)
        b.text = field_value.decode('utf-8')
        tmp.append(b)

        add = etree.Element('add')
        add.append(tmp)
        return add


class EAC(Common):
    def __init__(self, eac_input, output_folder, transforms, url_base):
        self.output_folder = output_folder

        self.eac_input = eac_input
        self.eac_transform = os.path.join(transforms, 'eac.xsl')

        self.url_base = url_base

        self.setup()

    def run(self):
        for (dirpath, dirnames, filenames) in os.walk(self.eac_input):
            for f in filenames:
                src = os.path.join(dirpath, f)
                try:
                    doc = etree.parse(src)
                except:
                    log.error("Couldn't process: %s" % src)
                    log.error(sys.exc_info()[1])
                    continue
                    
    def setup(self):
        # walk the path and process the content
        log.info('Setting up the required folder structure')
        output_folder = os.path.join(self.output_folder, 'eac') 
        if not os.path.exists(output_folder):
            log.debug("Creating: %s" % output_folder)
            os.makedirs(output_folder)
 
        # ensure we have the required folder structure
        solr = os.path.join(output_folder, 'solr')
        if not os.path.exists(solr):
            log.debug("Creating: %s" % solr)
            os.makedirs(solr)

        # ensure we have the required folder structure
        eac_original = os.path.join(output_folder, 'original')
        if not os.path.exists(eac_original):
            log.debug("Creating: %s" % eac_original)
            os.makedirs(eac_original)


class MODS(Common):
    def __init__(self, mods_input, output_folder, transforms, url_base):
        self.output_folder = output_folder

        self.mods_input = mods_input
        self.mods_transform = os.path.join(transforms, 'mods.xsl')

        self.url_base = url_base

        self.setup()

    def run(self):
        for (dirpath, dirnames, filenames) in os.walk(self.mods_input):
            for f in filenames: 
                file_basename = f
                src = os.path.join(dirpath, f)
                d = self.transform_record(src, self.mods_transform)

                if d is not None:
                    output_file = os.path.join(self.output_folder, 'mods/solr', file_basename)
                    f = open(output_file, 'w')
                    f.write(etree.tostring(d, pretty_print=True))
                    f.close()

                    tgt = os.path.join(self.output_folder, 'mods', 'original', file_basename)
                    log.debug("Copying over the original mods record: %s" % src)
                    shutil.copyfile(src, tgt)

    def setup(self):
        # walk the path and process the content
        log.info('Setting up the required folder structure')
        output_folder = os.path.join(self.output_folder, 'mods') 
        if not os.path.exists(output_folder):
            log.debug("Creating: %s" % output_folder)
            os.makedirs(output_folder)
 
        # ensure we have the required folder structure
        solr = os.path.join(output_folder, 'solr')
        if not os.path.exists(solr):
            log.debug("Creating: %s" % solr)
            os.makedirs(solr)

        # ensure we have the required folder structure
        mods_original = os.path.join(output_folder, 'original')
        if not os.path.exists(mods_original):
            log.debug("Creating: %s" % mods_original)
            os.makedirs(mods_original)

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
        log.info("Transforming: %s" % doc)
        d = xsl(tree)

        log.debug("Metadata\n%s" % etree.tostring(d, pretty_print=True))
        return d
     

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

    input_folder = cfg.get('General', 'input') if (cfg.has_section('General') and cfg.has_option('General', 'input')) else None
    output_folder = cfg.get('General', 'output') if (cfg.has_section('General') and cfg.has_option('General', 'output')) else None
    transforms = cfg.get('General', 'transforms') if (cfg.has_section('General') and cfg.has_option('General', 'transforms')) else None
    url_base = cfg.get('General', 'url_base') if (cfg.has_section('General') and cfg.has_option('General', 'url_base')) else None
    solr = cfg.get('General', 'solr') if (cfg.has_section('General') and cfg.has_option('General', 'solr')) else None
 
    # check the arguments
    if not os.path.exists(input_folder):
        log.error("Does %s exist?" % input_folder)
        sys.exit()

    if not os.path.exists(output_folder):
        os.mkdir(output_folder)

    if (args.crawl and args.mods) is not None:
        input_folder_mods = os.path.join(input_folder, args.mods)
        log.debug("Processing: '%s'. Output: '%s'." % (input_folder_mods, output_folder))
        mods = MODS(input_folder_mods, output_folder, transforms, url_base)
        mods.run()

    if (args.crawl and args.eac) is not None:
        input_folder_eac = os.path.join(input_folder, args.eac)
        log.debug("Processing: '%s'. Output: '%s'." % (input_folder_eac, output_folder))
        eac = EAC(input_folder_eac, output_folder, transforms, url_base)
        eac.run()

    if args.post is not None:
        log.info("Posting the data in: %s" % output_folder)
        i = Index(solr)
        i.clean()
        i.commit()
        i.optimize()

        # walk the path looking for the solr folder
        for (dirpath, dirnames, filenames) in os.walk(output_folder):
            if os.path.basename(dirpath) == 'solr':
                for f in filenames:
                    solr_doc = os.path.join(dirpath, f)
           
                    doc = etree.parse(solr_doc)
                    i.submit(etree.tostring(doc), solr_doc)
                i.commit()
                i.optimize()

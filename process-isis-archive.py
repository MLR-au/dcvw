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

class MODS(Common):
    def __init__(self, mods_input, eac_input, output_folder, transforms, url_base):
        self.output_folder = output_folder

        self.mods_input = mods_input
        self.mods_transform = os.path.join(transforms, 'mods.xsl')

        self.eac_input = eac_input
        self.eac_transform = os.path.join(transforms, 'eac.xsl')

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
     

class Crawler(Common):
    def __init__(self, input_folder, output_folder, transforms, url_base):
        self.input_folder = input_folder
        self.output_folder = output_folder
        self.transform = os.path.join(transforms, 'isis.xsl')
        self.url_base = url_base

    def run(self):

        # read in the volume metadata
        metadata_file = glob(os.path.join(self.input_folder, '*_metadata.mods.xml'))[0]
        metadata = self.get_metadata(metadata_file)

        # setup 
        volume = os.path.basename(self.input_folder)
        output_folder = self.setup(volume)

        # walk the path and process the content
        for (dirpath, dirnames, filenames) in os.walk(self.input_folder):

            tail = os.path.basename(dirpath)
            if tail == 'jpeg':
                # copy over the large and create the thumbnail
                log.debug("Processing images at: %s" % dirpath)
                self.process_images(filenames, output_folder)

            elif tail == 'txt':
                # create a solr record for each text file
                url_base = os.path.join(self.url_base, volume)
                self.create_solr_records(filenames, output_folder, metadata, url_base)

            elif tail == 'pdf':
                # copy over the pdf
                for f in filenames:
                    src = os.path.join(dirpath, f)
                    tgt = os.path.join(output_folder, 'pdf', f)
                    log.debug("Copying over the pdf: %s" % src)
                    shutil.copyfile(src, tgt)


    def setup(self, volume):
        """Setup the required output folder structure"""
        log.info('Setting up the required folder structure')
        output_folder = os.path.join(self.output_folder, volume) 
        if not os.path.exists(output_folder):
            log.debug("Creating: %s" % output_folder)
            os.makedirs(output_folder)
 
        # ensure we have the required folder structure
        solr = os.path.join(output_folder, 'solr')
        if not os.path.exists(solr):
            log.debug("Creating: %s" % solr)
            os.makedirs(solr)

        # ensure we have the required folder structure
        pdf = os.path.join(output_folder, 'pdf')
        if not os.path.exists(pdf):
            log.debug("Creating: %s" % pdf)
            os.makedirs(pdf)

        return output_folder

    def get_metadata(self, metadata_file):
        """Extract the item metadata and return it as an lxml document"""
        log.debug('Extracting the item metadata')
        try:
            log.debug("Reading in XSL transform to process metadata_file: %s" % self.transform)
            xsl = etree.parse(self.transform)
            xsl.xinclude()
            xsl = etree.XSLT(xsl)
        except IOError:
            log.error("No such transform: %s" % self.transform)
            return
        except etree.XSLTParseError:
            log.error("Check the stylesheet; I can't parse it! %s" % self.transform)
            return

        # read in the metadata file 
        log.debug("Reading in the metadata file: %s" % metadata_file)
        tree = etree.parse(metadata_file)

        # transform it!
        log.debug("Transforming the document")
        d = xsl(tree)

        #d = self.add_field(d, 'group', "%s-%s" % (bibrecid, item))

        log.debug("Metadata\n%s" % etree.tostring(d, pretty_print=True))
        return d 

    def process_images(self, filenames, output_folder):
        log.info('Processing the image set')
        output_folder = os.path.join(output_folder, 'jpg')
        if not os.path.exists(output_folder):
            log.debug("Creating: %s" % output_folder)
            os.makedirs(output_folder)

        large_images = os.path.join(output_folder, 'large')
        if not os.path.exists(large_images):
            log.debug("Creating: %s" % large_images)
            os.makedirs(large_images)

        thumb_images = os.path.join(output_folder, 'thumb')
        if not os.path.exists(thumb_images):
            log.debug("Creating: %s" % thumb_images)
            os.makedirs(thumb_images)

        for f in filenames:

            # file fully qualified path
            file_full_path = os.path.join(self.input_folder, 'jpeg', f)

            large_file = os.path.join(large_images, f)
            thumb_file = os.path.join(thumb_images, f)
             
            # copy the large image to expected location if it's not there or it's broken
            if not os.path.exists(large_file) or os.stat(large_file).st_size == 0:
                log.debug("Copying large file: %s" % file_full_path)
                shutil.copyfile(file_full_path, large_file)

            # if we don't have a thumbnail - create it
            if not os.path.exists(thumb_file) or os.stat(large_file).st_size == 0:
                log.debug("Creating thumbnail for %s" % file_full_path)
                try:
                    p = subprocess.check_call("/usr/bin/convert -thumbnail 100 %s %s" % (file_full_path, thumb_file), stderr=subprocess.PIPE, shell=True)
                except:
                    log.error("Couldn't create thumbnail for: %s" % file_full_path)

                
    def create_solr_records(self, filenames, output_folder, d, url_base):
        log.info('Creating the SOLR stub records')

        images = os.path.join(output_folder, 'jpg', 'large')
        solr = os.path.join(output_folder, 'solr')
        for f in filenames:

            fname = os.path.join(self.input_folder, 'txt', f)
            log.debug("Reading: %s" % fname)
            fh = open(fname, 'r')
            content = fh.read()
            fh.close()

            basename = os.path.splitext(os.path.basename(f))[0]

            rid = os.path.join(url_base, 'solr', basename)
            large_image = os.path.join(url_base, 'jpg/large', "%s.jpg" % basename)
            thumb_image = os.path.join(url_base, 'jpg/thumb', "%s.jpg" % basename)
            pdf = os.path.join(url_base, 'pdf', "%s.pdf" % basename)

            doc = self.add_field(copy.deepcopy(d), 'id', "%s.xml" % rid)
            doc = self.add_field(doc, 'large_image', large_image)
            doc = self.add_field(doc, 'thumb_image', thumb_image)
            doc = self.add_field(doc, 'pdf', pdf)
            doc = self.add_field(doc, 'text', content)

            fh = os.path.join(solr, "%s.xml" % basename)
            log.debug("Writing metatdata to: %s " % fh)
            f = open(fh, 'w')
            f.write(etree.tostring(doc, pretty_print=True))
            f.close()


if __name__ == "__main__":
    
    # read and check the options
    parser = argparse.ArgumentParser(description='DCVW ISIS Batch Processor')

    parser.add_argument('--config',   dest='config', required=True, help='The path to the config file.')
    parser.add_argument('--volume',   dest='volume', default=None, help='The volume to process.')
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
    if args.volume is None and (args.mods and args.eac) is None and args.crawl is not None:
        log.error("Must specifiy either --volume or --mods and --eac")
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

    if (args.crawl and args.volume) is not None:
        ### CRAWLER
        input_folder = os.path.join(input_folder, args.volume)
        log.debug("Processing: '%s'. Output: '%s'." % (input_folder, output_folder))
        crawler = Crawler(input_folder, output_folder, transforms, url_base)
        crawler.run()

    if (args.crawl and args.mods and args.eac) is not None:
        input_folder_eac = os.path.join(input_folder, args.eac)
        input_folder_mods = os.path.join(input_folder, args.mods)
        log.debug("Processing: '%s, %s'. Output: '%s'." % (input_folder_mods, input_folder_eac, output_folder))
        mods = MODS(input_folder_mods, input_folder_eac, output_folder, transforms, url_base)
        mods.run()


    if args.post is not None:
        log.info("Posting the data in: %s" % output_folder)
        i = Index(solr)

        # walk the path looking for the solr folder
        for (dirpath, dirnames, filenames) in os.walk(output_folder):
            if os.path.basename(dirpath) == 'solr':
                for f in filenames:
                    solr_doc = os.path.join(dirpath, f)
           
                    doc = etree.parse(solr_doc)
                    i.submit(etree.tostring(doc), solr_doc)
                i.commit()
                i.optimize()

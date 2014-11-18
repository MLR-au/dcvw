#!/usr/bin/env python


import argparse
import ConfigParser
from lxml import etree
import os
import os.path
import sys
from fnmatch import fnmatch
import subprocess
import copy
import shlex

# get the logger
import logging
log = logging.getLogger(__name__)

from Index import *

class Crawler:
    def __init__(self, input_folder, n, output_folder, transforms, url_base):
        self.input_folder = input_folder
        if n is not None:
            self.stop_after = int(n)
        else:
            self.stop_after = n
        self.output_folder = output_folder
        self.transforms = transforms
        self.url_base = url_base

    def run(self):
        # walk the path looking for XML files matching the bib code
        count = 0
        for (dirpath, dirnames, filenames) in os.walk(self.input_folder):
            for f in filenames:
                if fnmatch(f, '*-item.xml'):
                    count += 1
                    # looks like a folder we want to process

                    datafiles = {}
                    datafiles['dirpath'] = dirpath
                    datafiles['metadata_files'] = []
                    datafiles['metadata_files'].append(os.path.join(dirpath, f))

                    bibrecid = f.split('-')[0]
                    item = f.split('-')[1]
                    log.info("Processing: %s: %s-%s" % (count, bibrecid, item))

                    for f in filenames:
                        if fnmatch(f, '*-cat.xml'):
                            datafiles['metadata_files'].append(os.path.join(dirpath, f))

                        #elif fnmatch(f, '*-exiftool.txt'):
                        #    datafiles['metadata_files'].append(os.path.join(dirpath, f))

                        elif fnmatch(f, '*.pdf'):
                            datafiles['pdf_data_file'] = f


                    log.debug(datafiles);

                    # setup 
                    output_folder = self.setup(bibrecid, item)

                    # get the metadata
                    metadata = self.get_metadata(datafiles['metadata_files'], bibrecid, item)
                    if metadata == None:
                        log.error("Metadata file invalid. Not continuing.")
                        if (self.stop_after == count):
                            sys.exit()
                        continue

                    # process any images
                    image_paths = [ os.path.join(datafiles['dirpath'], d) for d in [ 'TIFF', 'TIF', 'tiff', 'tif' ] ]
                    found_images = False;
                    for path in image_paths:
                        if os.path.exists(path):
                            found_images = True;
                            self.process_images(path, output_folder)

                            # create a solr record for each image found
                            url_base = os.path.join(self.url_base, bibrecid, item)
                            self.create_solr_stub_records(output_folder, metadata, url_base)

                            self.process_ocr_data(os.path.join(datafiles['dirpath'], 'OCR'), output_folder)
                            break
                    
                    if not found_images:
                        log.error("No images found! %s, %s" % (bibrecid, item))

                    if self.stop_after is not None and self.stop_after == count:
                        sys.exit()

                    log.info("")

    def setup(self, bibrecid, item):
        """Setup the required output folder structure"""
        log.info('Setting up the required folder structure')
        output_folder = os.path.join(self.output_folder, bibrecid, item) 
        if not os.path.exists(output_folder):
            log.debug("Creating: %s" % output_folder)
            os.makedirs(output_folder)
 
        # ensure we have the required folder structure
        solr = os.path.join(output_folder, 'solr')
        if not os.path.exists(solr):
            log.debug("Creating: %s" % solr)
            os.makedirs(solr)

        return output_folder

    def get_metadata(self, metadata_files, bibrecid, item):
        """Extract the item metadata and return it as an lxml document"""
        log.debug('Extracting the item metadata')

        for m in metadata_files:
            if fnmatch(m, '*-item.xml'):
                transform = os.path.join(self.transforms, 'udc-item.xsl')
                d = self.process_document(m, transform)
                if d == None:
                    log.error("Couldn't get any metadata from: %s" % m)
                    return
                d = self.add_field(d, 'bibrecid', bibrecid)
                d = self.add_field(d, 'item', item)
                d = self.add_field(d, 'group', "%s-%s" % (bibrecid, item))

            #elif fnmatch(m, '*-cat.xml'):
            #    transform = os.path.join(self.transforms, 'udc-cat.xsl')
            #    e = self.process_document(m, transform)

        log.debug("Metadata\n%s" % etree.tostring(d, pretty_print=True))
        return d 

    def process_document(self, d, transform):
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

        # read in the metadata file 
        log.debug("Reading in the metadata file: %s" % d)
        try:
            tree = etree.parse(d)
        except etree.XMLSyntaxError:
            log.error("Invalid metadata file: %s" % d)
            return

        # transform it!
        log.debug("Transforming the document")
        d = xsl(tree)
        return d

    def add_field(self, doc, field_name, field_value):
        tmp = doc.xpath('/add/doc')[0]

        # add the record and item metadata 
        b = etree.Element('field', name=field_name)
        b.text = field_value
        tmp.append(b)

        add = etree.Element('add')
        add.append(tmp)
        return add

    def process_images(self, path, output_folder):
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

        for f in os.listdir(path):
            # have we already converted this file - skip it if we have
            file_basename = os.path.basename(f).split('.')[0]

            # file fully qualified path
            file_full_path = os.path.join(path, f)

            # only handle image files in the specified format 
            extension = os.path.splitext(f)[1]
            if extension in [ '.tif', '.jp2' ]:

                large_file = os.path.join(large_images, "%s.jpg" % file_basename)
                thumb_file = os.path.join(thumb_images, "%s.jpg" % file_basename)
                 
                # if we don't have a large image - create it
                if not os.path.exists(large_file) or os.stat(large_file).st_size == 0:
                    log.debug("Creating jpeg for %s" % file_full_path)
                    large_file = "%s/%s.jpg" % (large_images, file_basename)
                    cmd = "convert %s -resample 200 -strip -resize '3000x3000>' -compress JPEG -quality 30 -depth 8 -unsharp '1.5x1+0.7+0.02' %s" % (file_full_path, large_file)
                    try:
                        p = subprocess.check_call(cmd, stderr=subprocess.PIPE, shell=True)
                    except:
                        log.error("Error creating large jpeg")
                        log.error("%s" % cmd)
                    #print ['convert', file_full_path, "%s/%s.jpg" % (large_images, file_basename) ]

                # if we don't have a thumbnail - create it
                if not os.path.exists(thumb_file) or os.stat(large_file).st_size == 0:
                    log.debug("Creating thumbnail for %s" % file_full_path)
                    cmd = "convert %s -thumbnail 100x200 -strip -compress JPEG -quality 20 -depth 8 %s/%s.jpg" % (large_file, thumb_images, file_basename)
                    try:
                        p = subprocess.check_call(cmd, stderr=subprocess.PIPE, shell=True)
                    except:
                        log.error("Error creating thumbnail")
                        log.error("%s" % cmd)

                continue
                
    def create_solr_stub_records(self, output_folder, d, url_base):
        log.info('Creating the SOLR stub records')
        images = os.path.join(output_folder, 'jpg', 'large')
        solr = os.path.join(output_folder, 'solr')

        files = os.listdir(images)
        total_pages = str(len(files))

        for f in files:
            basename = os.path.splitext(os.path.basename(f))[0]

            rid = os.path.join(url_base, 'solr', basename)
            large_image = os.path.join(url_base, 'jpg/large', "%s.jpg" % basename)
            thumb_image = os.path.join(url_base, 'jpg/thumb', "%s.jpg" % basename)
            
            doc = self.add_field(copy.deepcopy(d), 'id', "%s.xml" % rid)
            doc = self.add_field(doc, 'page', basename.split('-')[2])
            doc = self.add_field(doc, 'large_image', large_image)
            doc = self.add_field(doc, 'thumb_image', thumb_image)
            doc = self.add_field(doc, 'total_pages', total_pages)

            fh = os.path.join(solr, "%s.xml" % basename)
            log.debug("Writing metatdata to: %s " % fh)
            f = open(fh, 'w')
            f.write(etree.tostring(doc, pretty_print=True))
            f.close()

    def process_ocr_data(self, ocr_data, output_folder):
        log.info('Processing the OCR data')

        # walk the tree of output images
        for f in os.listdir(os.path.join(output_folder, 'jpg/large')):
            name = os.path.basename(f).split('.jpg')[0]
            ocr_data_file = os.path.join(ocr_data, "%s.xml" % name)
            solr_stub = os.path.join(output_folder, 'solr', "%s.xml" % name)

            # parse that file as it should have metadata in it
            tree = etree.parse(solr_stub)
            #print etree.tostring(tree)
            #print etree.tostring(element, pretty_print=True)
            log.debug("Writing OCR data to: %s" % solr_stub)
            text = self.get_ocr_text(ocr_data_file)
            tree = self.add_field(tree, 'text', text)

            fh = open(solr_stub, 'w')
            fh.write(etree.tostring(tree, pretty_print=True, method='xml'))
            fh.close()
                

        # for each: source the OCR - load it and extract text content
        # source the solr stub file - inject the text content

    def get_ocr_text(self, ocr_data_file):
        try:
            for event, element in etree.iterparse(ocr_data_file,
                tag = '{http://www.scansoft.com/omnipage/xml/ssdoc-schema3.xsd}page'):

                # construct the solr source filename
                source = element.xpath('n:body/n:section', namespaces = { 'n': 'http://www.scansoft.com/omnipage/xml/ssdoc-schema3.xsd' })[0]
                return " ".join(etree.tostring(element, method='text', encoding='unicode').split())
        except:
            pass

if __name__ == "__main__":
    
    # read and check the options
    parser = argparse.ArgumentParser(description='DCVW UDC Batch Processor')

    parser.add_argument('--config',   dest='config', required=True, help='The path to the config file.')
    parser.add_argument('--input',   dest='input', required=True, help='The path to the input data.')
    parser.add_argument('--output',   dest='output', help='The path to where the output should go.')
    parser.add_argument('--n', dest='n', default=None, help="Stop after processing this many items.")

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

    if not os.path.exists(args.config):
        log.error("Can't find that config file: %s" % args.config)
        sys.exit()

    # get the default configuration
    cfg = ConfigParser.SafeConfigParser()
    cfg.read(args.config)

    transforms = cfg.get('General', 'transforms') if (cfg.has_section('General') and cfg.has_option('General', 'transforms')) else None
    url_base = cfg.get('General', 'url_base') if (cfg.has_section('General') and cfg.has_option('General', 'url_base')) else None
    solr = cfg.get('General', 'solr') if (cfg.has_section('General') and cfg.has_option('General', 'solr')) else None
    log.debug("Processing: '%s'. Output: '%s'. Solr: '%s'" % (args.input, args.output, solr))
 
    # check the arguments
    if not os.path.exists(args.input):
        log.error("Does %s exist?" % args.input)
        sys.exit()

    if args.output is not None and not os.path.exists(args.output):
        os.mkdir(args.output)

    if args.crawl is not None:
        ### CRAWLER
        crawler = Crawler(args.input, args.n, args.output, transforms, url_base)
        crawler.run()

    if args.post is not None:
        log.info("Posting the data in: %s" % args.input)
        i = Index(solr)

        # walk the path looking for the solr folder
        count = 0
        for (dirpath, dirnames, filenames) in os.walk(args.input):
            if os.path.basename(dirpath) == 'solr':
                count += 1
                log.info("Processing: %s: %s" % (count, dirpath))
                for f in filenames:
                    solr_doc = os.path.join(dirpath, f)
           
                    doc = etree.parse(solr_doc)
                    i.submit(etree.tostring(doc), solr_doc)


                i.commit()
                i.optimize()

            if args.n is not None and count == int(args.n):
                sys.exit()

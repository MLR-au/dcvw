#!/usr/local/scholarly-python2/bin/python


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
    def __init__(self, input_folder, output_folder, transforms, url_base):
        self.input_folder = input_folder
        self.output_folder = output_folder
        self.transform = os.path.join(transforms, 'udc.xsl')
        self.url_base = url_base

    def run(self):
        # walk the path looking for XML files matching the bib code
        for (dirpath, dirnames, filenames) in os.walk(self.input_folder):
            for f in filenames:
                if fnmatch(f, 'b???????.xml'):

                    # looks like a folder we want to process
                    datafiles = {}
                    for f in filenames:
                        if fnmatch(f, 'b???????.xml'):
                            datafiles['metadata_file'] = f

                        elif fnmatch(f, 'b???????-?????-?????.pdf'):
                            datafiles['pdf_data_file'] = f

                        elif fnmatch(f, 'b???????-omnipage.xml'):
                            datafiles['ocr_data_file'] = f

                    datafiles['dirpath'] = dirpath
                    bibrecid = datafiles['metadata_file'].split('.xml')[0]
                    item = datafiles['pdf_data_file'].split('-')[1]

                    log.info("Processing: %s-%s" % (bibrecid, item))

                    # setup 
                    output_folder = self.setup(bibrecid, item)

                    # get the metadata
                    metadata_file = os.path.join(datafiles['dirpath'], datafiles['metadata_file'])
                    metadata = self.get_metadata(metadata_file, bibrecid, item)

                    # process any images
                    image_paths = [ os.path.join(datafiles['dirpath'], d) for d in [ 'TIFF', 'TIF', 'JP2' ] ]
                    for path in image_paths:
                        if os.path.exists(path):
                            log.debug("Processing images at: %s" % path)
                            self.process_images(path, output_folder)
                            break

                    # create a solr record for each image found
                    url_base = os.path.join(self.url_base, bibrecid, item)
                    self.create_solr_stub_records(output_folder, metadata, url_base)

                    if datafiles.has_key('ocr_data_file'):
                        self.process_ocr_data(os.path.join(datafiles['dirpath'], datafiles['ocr_data_file']), output_folder)

                    log.info('')

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

    def get_metadata(self, metadata_file, bibrecid, item):
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

        d = self.add_field(d, 'bibrecid', bibrecid)
        d = self.add_field(d, 'item', item)
        d = self.add_field(d, 'group', "%s-%s" % (bibrecid, item))

        log.debug("Metadata\n%s" % etree.tostring(d, pretty_print=True))
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
        output_folder = os.path.join(output_folder, 'JPG')
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
                    p = subprocess.check_call(['/usr/bin/convert',  file_full_path, "%s/%s.jpg" % (large_images, file_basename) ], stderr=subprocess.PIPE)
                    #print ['convert', file_full_path, "%s/%s.jpg" % (large_images, file_basename) ]

                # if we don't have a thumbnail - create it
                if not os.path.exists(thumb_file) or os.stat(large_file).st_size == 0:
                    log.debug("Creating thumbnail for %s" % file_full_path)
                    p = subprocess.check_call("/usr/bin/convert -thumbnail 100 %s %s/%s.jpg" % (file_full_path, thumb_images, file_basename), stderr=subprocess.PIPE, shell=True)

                continue
                
    def create_solr_stub_records(self, output_folder, d, url_base):
        log.info('Creating the SOLR stub records')
        images = os.path.join(output_folder, 'JPG', 'large')
        solr = os.path.join(output_folder, 'solr')
        for f in os.listdir(images):
            basename = os.path.splitext(os.path.basename(f))[0]

            rid = os.path.join(url_base, 'solr', basename)
            large_image = os.path.join(url_base, 'JPG/large', "%s.jpg" % basename)
            thumb_image = os.path.join(url_base, 'JPG/thumb', "%s.jpg" % basename)

            doc = self.add_field(copy.deepcopy(d), 'id', "%s.xml" % rid)
            doc = self.add_field(doc, 'page', basename.split('-')[2])
            doc = self.add_field(doc, 'large_image', large_image)
            doc = self.add_field(doc, 'thumb_image', thumb_image)

            fh = os.path.join(solr, "%s.xml" % basename)
            log.debug("Writing metatdata to: %s " % fh)
            f = open(fh, 'w')
            f.write(etree.tostring(doc, pretty_print=True))
            f.close()

    def process_ocr_data(self, ocr_data_file, output_folder):
        log.info('Processing the OCR data')
        count = 0
        for event, element in etree.iterparse(ocr_data_file,
            tag = '{http://www.scansoft.com/omnipage/xml/ssdoc-schema3.xsd}page'):

            count += 1

            # construct the solr source filename
            source = element.xpath('n:description/n:source', namespaces = { 'n': 'http://www.scansoft.com/omnipage/xml/ssdoc-schema3.xsd' })[0]
            fh = source.attrib['file'].split('\\')[-1:][0].split('.')[0]
            fh = os.path.join(output_folder, 'solr', "%s.xml" % fh)
            log.debug("Writing OCR data to: %s" % fh)

            # parse that file as it should have metadata in it
            tree = etree.parse(fh)
            tree = self.add_field(tree, 'text', " ".join(etree.tostring(element, method='text', encoding='unicode').split()))

            fh = open(fh, 'w')
            fh.write(etree.tostring(tree, pretty_print=True, method='xml'))
            fh.close()

if __name__ == "__main__":
    
    # read and check the options
    parser = argparse.ArgumentParser(description='DCVW UDC Batch Processor')

    parser.add_argument('--config',   dest='config', required=True, help='The path to the config file.')

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


    # get the default configuration
    cfg = ConfigParser.SafeConfigParser()
    cfg.read(args.config)

    input_folder = cfg.get('General', 'input') if (cfg.has_section('General') and cfg.has_option('General', 'input')) else None
    output_folder = cfg.get('General', 'output') if (cfg.has_section('General') and cfg.has_option('General', 'output')) else None
    transforms = cfg.get('General', 'transforms') if (cfg.has_section('General') and cfg.has_option('General', 'transforms')) else None
    url_base = cfg.get('General', 'url_base') if (cfg.has_section('General') and cfg.has_option('General', 'url_base')) else None
    solr = cfg.get('General', 'solr') if (cfg.has_section('General') and cfg.has_option('General', 'solr')) else None
    log.debug("Processing: '%s'. Output: '%s'. Solr: '%s'" % (input_folder, output_folder, solr))
 
    # check the arguments
    if not os.path.exists(input_folder):
        log.error("Does %s exist?" % input_folder)
        sys.exit()

    if not os.path.exists(output_folder):
        os.mkdir(output_folder)

    if args.crawl is not None:
        ### CRAWLER
        crawler = Crawler(input_folder, output_folder, transforms, url_base)
        crawler.run()

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

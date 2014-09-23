#!/usr/local/scholarly-python2/bin/python


import argparse
import logging
from lxml import etree
import os
import os.path
import sys
from fnmatch import fnmatch

# get the logger
log = logging.getLogger(__name__)

class Crawler:
    def __init__(self, input_folder, output_folder, transforms):
        self.input_folder = input_folder
        self.output_folder = output_folder

        self.transform = os.path.join(transforms, 'udc.xsl')

        log.debug(self.input_folder, self.output_folder)

    def run(self):
        # walk the path looking for XML files matching the bib code
        for (dirpath, dirnames, filenames) in os.walk(self.input_folder):
            for f in filenames:
                if fnmatch(f, 'b???????.xml'):
                    process_list = self.get_process_list(filenames)
                    process_list['dirpath'] = dirpath
                    print dirpath
                    process_list['bibrecid'] = process_list['metadata_file'].split('.xml')[0]
                    process_list['item'] = process_list['pdf_data_file'].split('-')[1]

                    self.process(process_list)

    def get_process_list(self, filenames):
        process_list = {}
        for f in filenames:
            if fnmatch(f, 'b???????.xml'):
                process_list['metadata_file'] = f

            elif fnmatch(f, 'b???????-?????-?????.pdf'):
                process_list['pdf_data_file'] = f

            elif fnmatch(f, 'b???????-omnipage.xml'):
                process_list['ocr_data_file'] = f

            elif fnmatch(f, 'b???????-?????-?????-exiftool.txt'):
                process_list['extra-data'] = f
        return process_list

    def process(self, dfs):

        # create the required output folders as self.output_folder, bibrecid, item
        output = os.path.join(self.output_folder, dfs['bibrecid'], dfs['item']) 
        if not os.path.exists(output):
            os.makedirs(output)
        solr = os.path.join(output, 'solr')
        if not os.path.exists(solr):
            os.makedirs(solr)

        try:
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
        tree = etree.parse(os.path.join(dfs['dirpath'], dfs['metadata_file']))

        # transform it!
        d = xsl(tree)
        #print etree.tostring(d, pretty_print=True)

        # look for a folder called JPG - and in there find the large and thumbnails
        path = os.path.join(dfs['dirpath'], 'JPG/large')
        if os.path.exists(path):
            files = [ os.path.join(path, f) for f in os.listdir(path) ]
            for f in files:
                fh = os.path.splitext(os.path.basename(f))[0]
                fh = os.path.join(solr, "%s.xml" % fh)
                log.debug("Writing metatdata to: %s " % fh)

                f = open(fh, 'w')
                f.write(etree.tostring(d, pretty_print=True))
                f.close()

        # extract the OCR data and add it to the solr documents
        if dfs.has_key('ocr_data_file'):
            count = 0
            for event, element in etree.iterparse(os.path.join(dfs['dirpath'], dfs['ocr_data_file']),
                tag = '{http://www.scansoft.com/omnipage/xml/ssdoc-schema3.xsd}page'):

                count += 1

                # construct the solr source filename
                source = element.xpath('n:description/n:source', namespaces = { 'n': 'http://www.scansoft.com/omnipage/xml/ssdoc-schema3.xsd' })[0]
                fh = source.attrib['file'].split('\\')[-1:][0].split('.')[0]
                fh = os.path.join(solr, "%s.xml" % fh)
                log.debug("Writing OCR data to: %s" % fh)

                # parse that file as it should have metadata in it
                tree = etree.parse(fh)
                tmp = tree.xpath('/add/doc')[0]

                # add the site metadata into the record
                text_data = etree.Element('field', name='text')
                text_data.text = " ".join(etree.tostring(element, method='text', encoding='unicode').split())
                tmp.append(text_data)

                add = etree.Element('add')
                add.append(tmp)

                fh = open(fh, 'w')
                fh.write(etree.tostring(add, pretty_print=True, method='xml'))
                fh.close()

if __name__ == "__main__":
    
    # read and check the options
    parser = argparse.ArgumentParser(description='DCVW UDC Batch Processor')

    parser.add_argument('--input',   dest='input', required=True, help='The path to the data folders.')
    parser.add_argument('--output',  dest='output', required=True, help='Where to store the output.')

    parser.add_argument('--crawl', dest='crawl', action='store_true', default=None,
        help='Only perform the crawl and transform stages.')
    parser.add_argument('--transforms', dest='transforms', required=True,
        help='Path to the transforms.')

    parser.add_argument('--post', dest='post', action='store_true', default=None,
        help='Only perform the post stage (includes index clean).')

    parser.add_argument('--clean', dest='clean', action='store_true', default=None,
        help="Wipe this site's data from the index first or not?")

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


    # check the arguments
    if not os.path.exists(args.input):
        log.error("Does %s exist?" % args.input)
        sys.exit()

    if not os.path.exists(args.output):
        os.mkdir(args.output)

    if args.crawl is not None:
        ### CRAWLER
        crawler = Crawler(args.input, args.output, args.transforms)
        crawler.run()

        ### TRANSFORMER
        ### Only do the crawl if the user is not requesting to specifically
        ###  process a single file; this is usually testing
        #indexer.transform(content)

    if args.post is not None:
        ### POSTER
        #indexer.post(args.solr, args.clean)
        pass


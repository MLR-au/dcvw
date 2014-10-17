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

if __name__ == "__main__":
    
    # read and check the options
    parser = argparse.ArgumentParser(description='DCVW Isis Helper')

    parser.add_argument('--input',   dest='input', required=True, help='The path to the source data.')
    parser.add_argument('--output',  dest='output', required=True, help='The path to where the output should be stored.')

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

    if not os.path.exists(args.output):
        os.mkdir(args.output)

    i = 0
    j = 0
    for (dirpath, dirnames, filenames) in os.walk(args.input):
        for f in filenames:
            i += 1

            output_folder = os.path.join(args.output, str("%05d" % j))
            file_basename = f
            src = os.path.join(dirpath, f)

            if not os.path.exists(output_folder):
                os.mkdir(output_folder)

            log.info("Processing: %s" % src)
            shutil.copy(src, output_folder)
            if i == 2000:
                j +=1 
                i = 0



# Batch processor to create solr records for each page of a digitised item

## Synopsis

The script expects to walk a filesystem tree in search of folders containing a file matching
the format b???????.xml. If a match is found, that folder is deemed to contain a digitised
item and the script will attempt to process it.

The batch process will attempt to create a solr record for each digitised page with the OCR
data for the page (if it's available) included. In addition, the script will create large and
thumbnail jpegs if they do not already exist.

## Features
* Agnostic to filesystem structure. A folder is deemed to be fit for processing if it contains
  a file matching the pattern: b???????.xml (This is the bibrecord file).
* Can convert TIFF and jpeg2000 images to jpegs useable on the web.
* Can extract metadata from the bibrecord file which is ingested into the solr record for each page.
* Can extract the OCR data from OmniPage output (if it exists).

## Invocation

```
The process is designed to be run in an automated fashion and it is idempotent. A typical invocation
by cron might be:
* /usr/share/batch/process-udx-archive.py --config /etc/batch/config --crawl --post

(This assumes the tool is installed in /usr/share/batch on the target system and configuration is located
at /etc/batch). Of course - you can just crawl or just post as well.

To get an overview of what the tool is doing add --info, e.g.:
* /usr/share/batch/process-udx-archive.py --config /etc/batch/config --crawl --post --info

And to see the gory detail, --debug, e.g:
* /usr/share/batch/process-udx-archive.py --config /etc/batch/config --crawl --post --debug

For help:
* /usr/share/batch/process-udx-archive.py --help
```

## Example config file

    [General]
    input:                          PATH to the data - this could be a local mount or just a folder of content
    output:                         PATH to the output folder
    transforms:                     /usr/share/batch/transforms
    url_base:                       The URL at which the output folder is accessible. This is required to be able to construct the URL links.
    solr:                           http://(URL to your solr server)/(CORE)




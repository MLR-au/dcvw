#!/bin/bash

./process-udc-archive.py --config config/udc-config --input /srv/udc/UDS-Archives/libcat/ --output /srv/data/DCVW --crawl --post
rsync -av /srv/data/DCVW/ 115.146.84.251:/srv/data/DCVW/
rsync -av /srv/data/DCVW/ 115.146.86.212:/srv/data/DCVW/
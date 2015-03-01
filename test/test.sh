#!/bin/bash

# hosts contants
DNSHOST=cs5700cdnproject.ccs.neu.edu
PORT=51151

while read uri
do
    cdnip=`dig +short -p $PORT @cs5700cdnproject.ccs.neu.edu cs5700cdn.example.com | head -1`
    time wget -O /dev/null http://$cdnip:$PORT$uri
done < wikilist.txt

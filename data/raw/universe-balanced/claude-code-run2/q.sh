#!/bin/bash
# $1 = query, $2 = outfile tag
q=$(python3 -c "import urllib.parse,sys;print(urllib.parse.quote(sys.argv[1]))" "$1")
curl -s -m 60 "https://archive.org/advancedsearch.php?q=${q}&fl%5B%5D=identifier&fl%5B%5D=title&fl%5B%5D=creator&fl%5B%5D=year&fl%5B%5D=date&rows=200&output=json" \
 | python3 -c "
import json,sys
d=json.load(sys.stdin)
for x in d['response']['docs']:
    c=x.get('creator')
    if isinstance(c,list): c='; '.join(c)
    print('\t'.join([str(x.get('year','')), str(c), str(x.get('title','')).replace('\t',' '), x['identifier']]))
" >> harvest/$2.tsv

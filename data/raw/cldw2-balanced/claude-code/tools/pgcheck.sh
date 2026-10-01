#!/bin/bash
# usage: pgcheck.sh ID [ID...]
for id in "$@"; do
  u="https://www.gutenberg.org/cache/epub/$id/pg$id.txt"
  n=$(curl -sL --max-time 90 "$u" | tr 'A-Z' 'a-z' | grep -oE 'windermere|grasmere|keswick|ambleside|derwent ?water|ullswater|borrowdale|helvellyn|skiddaw|coniston|rydal|langdale|wastwater|buttermere|patterdale|kendal|penrith|lake district|westmorland|westmoreland|cumberland|furness|scafell|sca ?fell|thirlmere|bassenthwaite|eskdale|whitehaven|cockermouth|lodore' | sort | uniq -c | sort -rn | head -8 | tr '\n' ' ')
  echo "$id :: $n"
done

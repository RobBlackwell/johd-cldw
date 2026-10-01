#!/bin/bash
for i in "$@"; do
  n=$(curl -sL --max-time 240 "https://archive.org/download/$i/${i}_djvu.txt" | tr 'A-Z' 'a-z' | grep -oE 'windermere|grasmere|keswick|ambleside|derwentwater|ullswater|borrowdale|helvellyn|skiddaw|coniston|rydal|langdale|buttermere|patterdale|kendal|penrith|lake district|westmorland|westmoreland|cumberland|furness|scafell|thirlmere|bassenthwaite|eskdale|whitehaven|cockermouth|lodore|bowness|hawkshead|brantwood|grisedale|winandermere' | sort | uniq -c | sort -rn | head -7 | tr '\n' ' ')
  echo "$i :: $n"
done

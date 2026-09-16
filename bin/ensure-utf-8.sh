#!/usr/bin/env sh

# Convert all UTF-16 xml files to UTF-8.

find .. -type f -name "*.xml" -print0 | while IFS= read -r -d '' file; do
    encoding=$(file -bI "$file" | awk -F'; charset=' '{print $2}')
    if [[ "$encoding" == "utf-16le" || "$encoding" == "utf-16be" || "$encoding" == "utf-16" ]]; then
        echo "Converting: $file ($encoding → utf-8)"
        tmp="${file}.tmp"
        iconv -f UTF-16 -t UTF-8 "$file" > "$tmp" && mv "$tmp" "$file"
    fi
done

TEMPLATE := prompt.txt.jinja
OUTPUT   := prompt.txt
SUBSET   := subset.jsonl
RENDER   := ../../../bin/render.py

# Auto-discover data files referenced via read_file("...") in the template,
# so `make` rebuilds whenever the template OR any file it pulls in changes.
INCLUDES := $(shell grep -oE 'read_file\(["'"'"'][^"'"'"']+["'"'"']\)' $(TEMPLATE) | sed -E 's/read_file\(["'"'"'](.*)["'"'"']\)/\1/')

.PHONY: all clean

all: $(OUTPUT)

BASE := ../prompt/prompt.txt.jinja

$(OUTPUT): $(TEMPLATE) $(BASE) $(RENDER) $(INCLUDES) $(SUBSET)
	python3 $(RENDER) $(TEMPLATE) $@

INPUT  := ../../interim/ld80-metadata/ld80-metadata.jsonl

$(SUBSET): $(INPUT)
	jq -c '{ID, Author, Title_full}' $(INPUT) > $@

clean:
	rm -f $(OUTPUT) $(SUBSET)

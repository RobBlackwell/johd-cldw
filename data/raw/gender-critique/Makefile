TEMPLATE := prompt.txt.jinja
OUTPUT   := prompt.txt
RENDER   := ../../../bin/render.py

# Auto-discover data files referenced via read_file("...") in the template,
# so `make` rebuilds whenever the template OR any file it pulls in changes.
INCLUDES := $(shell grep -oE 'read_file\(["'"'"'][^"'"'"']+["'"'"']\)' $(TEMPLATE) | sed -E 's/read_file\(["'"'"'](.*)["'"'"']\)/\1/')

.PHONY: all clean

all: $(OUTPUT)

$(OUTPUT): $(TEMPLATE) $(RENDER) $(INCLUDES)
	python3 $(RENDER) $(TEMPLATE) $@

clean:
	rm -f $(OUTPUT)

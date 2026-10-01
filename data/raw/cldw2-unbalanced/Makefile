PYTHON ?= python3
ROOT := ../../..
RENDER := $(ROOT)/bin/render.py

# Shared base template that prompt.txt.jinja extends.
BASE := $(ROOT)/data/raw/prompt/prompt.txt.jinja

.PHONY: all clean
all: prompt.txt

prompt.txt: prompt.txt.jinja $(BASE) $(RENDER)
	$(PYTHON) $(RENDER) $< $@

clean:
	rm -f prompt.txt

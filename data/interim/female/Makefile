# The female-authored texts the five claude-code runs found, as
# ../../../src/find-female.py prints them: one row per distinct work with the
# per-run ticks and the cldw column, then the CLDW women the runs lost.
#
#   make        # rebuild female.txt if the script or any corpus changed
#   make clean  # drop female.txt

ROOT := ../../..

DEPS := $(ROOT)/src/find-female.py

# The corpora it reads: the five runs' records and the original CLDW's
# metadata, which supplies the cldw column and the second table.
INPUTS := $(ROOT)/data/interim/ld80-metadata/ld80-metadata.jsonl \
          $(ROOT)/data/raw/cldw2-unbalanced/claude-code/texts.jsonl \
          $(ROOT)/data/raw/cldw2-balanced/claude-code/texts.jsonl \
          $(ROOT)/data/raw/universe-unbalanced/claude-code/texts.jsonl \
          $(ROOT)/data/raw/universe-balanced/claude-code/texts.jsonl \
          $(ROOT)/data/raw/universe-balanced/claude-code-run2/texts.jsonl

.PHONY: all clean

# Never leave a half-written female.txt behind when a run dies.
.DELETE_ON_ERROR:

all: female.txt

female.txt: $(DEPS) $(INPUTS)
	python3 $(ROOT)/src/find-female.py > $@

clean:
	rm -f female.txt

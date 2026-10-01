# The union of every corpus in the project, as ../../../src/union.py prints it:
# one row per distinct work, earliest first, with the per-corpus ticks, the
# summary table and the record/work counts.
#
#   make        # rebuild union.txt if the script or any corpus changed
#   make clean  # drop union.txt

ROOT := ../../..

# union.py borrows its normalisation from find-female.py and ub.py rather than
# copying it, so a change to either changes the merge.
DEPS := $(ROOT)/src/union.py $(ROOT)/src/find-female.py $(ROOT)/src/ub.py

# The corpora it pools: the original CLDW's metadata and the five runs.
INPUTS := $(ROOT)/data/interim/ld80-metadata/ld80-metadata.jsonl \
          $(ROOT)/data/raw/cldw2-unbalanced/claude-code/texts.jsonl \
          $(ROOT)/data/raw/cldw2-balanced/claude-code/texts.jsonl \
          $(ROOT)/data/raw/universe-unbalanced/claude-code/texts.jsonl \
          $(ROOT)/data/raw/universe-balanced/claude-code/texts.jsonl \
          $(ROOT)/data/raw/universe-balanced/claude-code-run2/texts.jsonl

.PHONY: all clean

# Never leave a half-written union.txt behind when a run dies.
.DELETE_ON_ERROR:

all: union.txt

union.txt: $(DEPS) $(INPUTS)
	python3 $(ROOT)/src/union.py > $@

clean:
	rm -f union.txt

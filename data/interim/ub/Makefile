# The run-to-run agreement of the two universe-balanced claude-code runs, as
# ../../../src/ub.py prints it: the record and distinct-work counts for each
# run, how many works they hold in common, and the overlap as a share of each
# run and as a Jaccard index.
#
#   make        # rebuild ub.txt if the script or either corpus changed
#   make clean  # drop ub.txt

ROOT := ../../..

# ub.py borrows its normalisation and title scoring from find-female.py rather
# than copying them, so a change to that script changes the merge.
DEPS := $(ROOT)/src/ub.py $(ROOT)/src/find-female.py

# The two corpora it compares: the one experiment that was run twice.
INPUTS := $(ROOT)/data/raw/universe-balanced/claude-code/texts.jsonl \
          $(ROOT)/data/raw/universe-balanced/claude-code-run2/texts.jsonl

.PHONY: all clean

# Never leave a half-written ub.txt behind when a run dies.
.DELETE_ON_ERROR:

all: ub.txt

ub.txt: $(DEPS) $(INPUTS)
	python3 $(ROOT)/src/ub.py > $@

clean:
	rm -f ub.txt

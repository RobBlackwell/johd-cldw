# Top-level build for the rendered prompts.
#
#   make           # render every prompt.txt that is out of date
#   make clean     # remove the rendered prompt.txt files and generated inputs
#   make rebuild   # clean, then render everything from scratch
#   make list      # show the variant directories that were discovered
#
# Each variant under data/raw/ carries its own Makefile; this one just
# fans out to them, so a new variant directory is picked up automatically
# as soon as it has a Makefile.
#
# The interim LD80 dataset (data/interim/ld80-metadata) is deliberately
# left out: it regenerates from a LakeDistrictCorpus checkout outside this
# repo, and its outputs are committed. Build it on demand with
#   make -C data/interim/ld80-metadata

MAKE_FLAGS := --no-print-directory

PROMPT_DIRS := $(patsubst %/Makefile,%,$(wildcard data/raw/*/Makefile))

BUILD_TARGETS := $(addprefix build-,$(PROMPT_DIRS))
CLEAN_TARGETS := $(addprefix clean-,$(PROMPT_DIRS))

.PHONY: all clean rebuild list $(BUILD_TARGETS) $(CLEAN_TARGETS)

all: $(BUILD_TARGETS)

$(BUILD_TARGETS):
	$(MAKE) $(MAKE_FLAGS) -C $(patsubst build-%,%,$@) all

clean: $(CLEAN_TARGETS)

$(CLEAN_TARGETS):
	$(MAKE) $(MAKE_FLAGS) -C $(patsubst clean-%,%,$@) clean

# Two passes so that -j never interleaves the clean with the rebuild.
rebuild:
	$(MAKE) $(MAKE_FLAGS) clean
	$(MAKE) $(MAKE_FLAGS) all

list:
	@$(foreach d,$(PROMPT_DIRS),echo $(d);)

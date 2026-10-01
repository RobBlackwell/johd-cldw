# CLDW3 / claude-code --- build an 80-text Lake District corpus from ../prompt.txt
#
# The run happens inside a Docker container so that it is sandboxed and
# repeatable: pinned image, pinned CLI version, no access to anything on the
# host except this directory and the Claude credential store. It is fully
# non-interactive --- permissions are pre-granted inside the sandbox rather
# than prompted for.
#
#   make            # build the image (if needed) and produce results.txt
#   make download   # fetch every text the run found into texts/
#   make login      # one-off interactive OAuth login into the sandbox creds
#   make shell      # poke around inside the sandbox
#   make clean      # strip the directory back to Dockerfile + Makefile
#   make distclean  # also drop the image
#
# Outputs:
#   trace.jsonl   full stream-json transcript of the run (every turn, tool call)
#   results.txt   the model's final answer, one JSON object per line (JSONL)
#   trace.txt     just the model's commentary from the trace, as plain prose
#   run-info.txt  what was run, with what versions, when --- keep with the data
#
# `make download` adds:
#   texts/        the full texts, one file per corpus line, plus failures.txt
#                 naming the texts that could not be fetched

# ---- knobs ------------------------------------------------------------------

PYTHON         ?= python3
MODEL          ?= opus
# How many texts ../prompt.txt asks for; a short run is a failed run.
EXPECTED       ?= 80
CLAUDE_VERSION ?= 2.1.267
IMAGE          ?= cldw3-claude-code:$(CLAUDE_VERSION)

# Tools the model is allowed: web search/fetch for finding texts, Bash for
# curl-ing and checking candidate download URLs, plus the file tools it needs
# to keep notes while it works.
TOOLS ?= Bash,WebFetch,WebSearch,Read,Write,Edit,Glob,Grep

# Credential store for the sandbox, kept outside the repo. Populated by
# `make login`. Every variant's harness defaults to this same path, so one
# login serves them all.
CREDS ?= $(HOME)/.claude-docker

ROOT    := ../../../..
PROCESS := $(ROOT)/bin/process-traces.py

PROMPT  := ../prompt.txt
TRACE   := trace.jsonl
PROSE   := trace.txt
RESULTS := results.txt
RUNINFO := run-info.txt
STAMP   := .image.stamp

# ---- sandbox ----------------------------------------------------------------

# --cap-drop/--no-new-privileges: the container gets no privileges it does not
# need, and --user runs it as you rather than root (Claude Code refuses to
# skip permission prompts as root, and it keeps generated files yours). Only
# this directory and the credential store are mounted, so the rest of the host
# --- including the rest of this repo --- is invisible to the run.
# Networking is left on: the whole point is fetching texts from the web.
DOCKER_RUN := docker run --rm -i \
	--cap-drop ALL \
	--security-opt no-new-privileges \
	--user "$(shell id -u):$(shell id -g)" \
	-e HOME=/home/claude \
	-v "$(CURDIR)":/work \
	-v "$(CREDS)":/home/claude \
	-w /work

# Pass through non-interactive credentials when the caller has them, so this
# also works in CI without a mounted OAuth login.
ifdef CLAUDE_CODE_OAUTH_TOKEN
DOCKER_RUN += -e CLAUDE_CODE_OAUTH_TOKEN
endif
ifdef ANTHROPIC_API_KEY
DOCKER_RUN += -e ANTHROPIC_API_KEY
endif

# --permission-mode bypassPermissions: pre-grant everything, since nobody is
# there to answer a prompt and the container is the security boundary.
# --strict-mcp-config: ignore any MCP servers in the credential store, so the
# run depends only on what is pinned here.
CLAUDE_ARGS := -p \
	--model $(MODEL) \
	--output-format stream-json --verbose \
	--tools "$(TOOLS)" \
	--permission-mode bypassPermissions \
	--strict-mcp-config

.PHONY: all download login shell image clean distclean $(RUNINFO)

# Never leave a partial file behind when a recipe fails.
.DELETE_ON_ERROR:

all: $(RESULTS) $(PROSE)

# ---- image ------------------------------------------------------------------

image: $(STAMP)

$(STAMP): Dockerfile
	docker build --build-arg CLAUDE_VERSION=$(CLAUDE_VERSION) -t $(IMAGE) .
	docker image inspect --format '{{.Id}}' $(IMAGE) > $@

# ---- the run ----------------------------------------------------------------

# Written to a temp file and moved into place, so an aborted or failed run does
# not leave a half-written trace.jsonl that make would treat as up to date.
$(TRACE): $(PROMPT) $(STAMP)
	@test -f "$(CREDS)/.claude/.credentials.json" \
	  || test -n "$$CLAUDE_CODE_OAUTH_TOKEN$$ANTHROPIC_API_KEY" \
	  || { echo "No sandbox credentials: run 'make login' first." >&2; exit 1; }
	$(DOCKER_RUN) $(IMAGE) claude $(CLAUDE_ARGS) < $(PROMPT) > $@.tmp
	@jq -e 'select(.type=="result") and (.is_error | not)' $@.tmp >/dev/null \
	  || { echo "Run failed: $$(jq -r 'select(.type=="result") | .result' $@.tmp)" >&2; \
	       mv $@.tmp $@.failed; echo "Trace kept as $@.failed" >&2; exit 1; }
	mv $@.tmp $@

# The final assistant message is the corpus; everything else in the trace is
# working. Drop any line that is not a JSON object so stray prose cannot end
# up in the dataset.
$(RESULTS): $(TRACE)
	jq -r 'select(.type=="result") | .result' $< \
	  | jq -R -c 'fromjson? | select(type=="object")' > $@.tmp
	@n=$$(grep -c . $@.tmp); \
	  test "$$n" -ge $(EXPECTED) \
	  || { echo "Only $$n JSONL objects parsed from $< (expected $(EXPECTED)); inspect the trace." >&2; \
	       rm -f $@.tmp; exit 1; }
	mv $@.tmp $@
	$(MAKE) --no-print-directory $(RUNINFO)
	@echo "$@: $$(wc -l < $@) texts"

# The prose the model wrote between its tool calls --- its account of what it
# was doing --- lifted out of the trace so it can be read, and quoted, without
# a megabyte of tool traffic in the way.
$(PROSE): $(TRACE) $(PROCESS)
	$(PYTHON) $(PROCESS) $< -o $@

$(RUNINFO):
	@{ \
	    echo "date:           $$(date -u +%Y-%m-%dT%H:%M:%SZ)"; \
	    echo "model:          $(MODEL)"; \
	    echo "claude version: $(CLAUDE_VERSION)"; \
	    echo "image:          $(IMAGE)"; \
	    echo "image id:       $$(cat $(STAMP))"; \
	    echo "prompt sha256:  $$(shasum -a 256 $(PROMPT) | cut -d' ' -f1)"; \
	    echo "tools:          $(TOOLS)"; \
	  } > $@

# ---- the texts themselves ---------------------------------------------------

# Every line of $(CORPUS) carries a download_url the run claimed was directly
# retrievable; `make download` puts that claim to the test and leaves what
# came back in $(TEXTS_DIR)/. Links rot, repositories throttle, and some of
# what a run reports was never retrievable in the first place, so a text that
# will not download is skipped rather than fatal: it is named on stderr as it
# happens, and listed with the reason in $(FAILURES).
#
# Files are named <line number>-<basename of the URL>, so a download can be
# traced back to the line of $(CORPUS) that asked for it. Whatever is already
# there is left alone, so a second `make download` retries only the failures
# --- but note that `make clean` takes $(TEXTS_DIR) with everything else.

CORPUS    ?= texts.jsonl
TEXTS_DIR ?= texts
FAILURES  := $(TEXTS_DIR)/failures.txt

# Follow redirects, treat an HTTP error as a failure rather than saving the
# error page under the name of a text, retry what is worth retrying, and give
# up on a text rather than hang on it. SLEEP pauses between texts so that
# eighty fetches in a row do not look like an attack to the repository.
CURL_ARGS ?= --location --fail --silent --show-error \
	--retry 3 --retry-delay 2 --retry-connrefused \
	--connect-timeout 20 --max-time 600
SLEEP     ?= 1

download:
	@test -f $(CORPUS) \
	  || { echo "No $(CORPUS) here --- nothing to download." >&2; exit 1; }
	@mkdir -p $(TEXTS_DIR)
	@: > $(FAILURES)
	@tab=$$(printf '\t'); \
	jq -r '[(if (.download_url // "") == "" then "-" else .download_url end), \
	        (.title // "")] | @tsv' $(CORPUS) \
	  | awk -F'\t' '{ printf "%03d\t%s\t%s\n", NR, $$1, $$2 }' \
	  | while IFS="$$tab" read -r n url title; do \
	      if [ "$$url" = "-" ]; then \
	        printf '%s\t%s\t%s\n' "$$n" "no download_url" "$$title" >> $(FAILURES); \
	        echo "skip $$n  no download_url: $$title" >&2; \
	        continue; \
	      fi; \
	      name=$$(basename "$$url" | sed 's/[^A-Za-z0-9._-]/_/g'); \
	      case "$$name" in ''|.|..) name=download;; esac; \
	      out=$(TEXTS_DIR)/$$n-$$name; \
	      if [ -s "$$out" ]; then echo "have $$out"; continue; fi; \
	      echo "get  $$out"; \
	      if curl $(CURL_ARGS) -o "$$out.part" "$$url"; then rc=0; else rc=$$?; fi; \
	      if [ "$$rc" -eq 0 ] && [ -s "$$out.part" ]; then \
	        mv "$$out.part" "$$out"; \
	      else \
	        rm -f "$$out.part"; \
	        if [ "$$rc" -eq 0 ]; then why="empty response"; \
	        else why="curl exit $$rc"; fi; \
	        printf '%s\t%s\t%s\t%s\n' "$$n" "$$why" "$$title" "$$url" >> $(FAILURES); \
	        echo "FAIL $$n  $$why: $$title" >&2; \
	      fi; \
	      sleep $(SLEEP); \
	    done
	@got=$$(find $(TEXTS_DIR) -type f ! -name failures.txt ! -name '*.part' \
	          | wc -l | tr -d ' '); \
	  bad=$$(grep -c . $(FAILURES) || true); \
	  echo "$(TEXTS_DIR): $$got downloaded, $$bad failed"; \
	  if [ "$$bad" -eq 0 ]; then rm -f $(FAILURES); \
	  else echo "failures listed in $(FAILURES)"; fi

# ---- housekeeping -----------------------------------------------------------

# One-off: log in to Claude inside the sandbox. The OAuth tokens land in
# $(CREDS) on the host and are reused (and refreshed) by every later run.
login: $(STAMP)
	@mkdir -p "$(CREDS)"
	@echo "Type /login at the Claude prompt, then /exit once you are signed in."
	docker run --rm -it \
	    --user "$(shell id -u):$(shell id -g)" \
	    -e HOME=/home/claude \
	    -v "$(CREDS)":/home/claude \
	    -w /work $(IMAGE) claude

shell: $(STAMP)
	$(DOCKER_RUN) -t $(IMAGE) bash

# The run scratches freely in this directory --- notes, helper scripts, part-
# downloaded sources --- and there is no listing them in advance, so clean is a
# whitelist rather than a list of outputs: keep the two files that define the
# run, delete everything else, including $(STAMP). The image itself survives,
# so the rebuild that restores the stamp is a cache hit; distclean drops it.
KEEP := Dockerfile Makefile

clean:
	@find . -mindepth 1 -maxdepth 1 \
	    $(foreach f,$(KEEP),! -name '$(f)') \
	    -exec rm -rf {} +

distclean: clean
	-docker image rm $(IMAGE)

# Makefile modeled after ../claude-code/Makefile
# Replace the copilot invocation flags below if your Copilot CLI differs.

MODEL   := auto
PROMPT  := ../prompt.txt
OUTPUT  := output.json
TEXTS   := texts.jsonl

.PHONY: all clean

all: $(TEXTS)

$(OUTPUT): $(PROMPT)
	@command -v copilot >/dev/null 2>&1 || (echo "copilot CLI not found in PATH" >&2; exit 1)
	copilot --prompt "$$(cat $(PROMPT))" --model $(MODEL) --output-format json \
		--allow-all-tools \
		--no-ask-user \
		> $@

$(TEXTS): $(OUTPUT)
	jq -r 'select(.type=="assistant.message") | .data.content' $< \
		| jq -R -c 'fromjson? | select(type=="object")' > $@

clean:
	rm -f $(OUTPUT) $(TEXTS)

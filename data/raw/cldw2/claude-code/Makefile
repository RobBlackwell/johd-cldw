MODEL   := sonnet
PROMPT  := ../prompt.txt
OUTPUT  := output.json
TEXTS   := texts.jsonl

.PHONY: all clean

all: $(TEXTS)

$(OUTPUT): $(PROMPT)
	claude -p --model $(MODEL) --output-format json \
		--verbose \
		--output-format stream-json \
		--tools "Bash,WebFetch,WebSearch" \
		--permission-mode bypassPermissions \
		< $(PROMPT) > $@

$(TEXTS): $(OUTPUT)
	jq -r 'select(.type=="result") | .result' $< \
		| jq -R -c 'fromjson? | select(type=="object")' > $@

clean:
	rm -f $(OUTPUT) $(TEXTS)

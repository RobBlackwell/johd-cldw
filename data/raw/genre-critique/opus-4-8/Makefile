MODEL   := opus
PROMPT  := ../prompt.txt
OUTPUT  := output.json

.PHONY: all clean

all: $(OUTPUT)

$(OUTPUT): $(PROMPT)
	claude -p --model $(MODEL) --output-format json \
		--verbose \
		--output-format stream-json \
		--tools "Bash,WebFetch,WebSearch" \
		--permission-mode bypassPermissions \
		< $(PROMPT) > $@

clean:
	rm -f $(OUTPUT) $(TEXTS)

MODEL   := gemini-3.1-pro-preview
PROMPT  := ../prompt.txt
OUTPUT  := output.json
ENDPOINT := https://generativelanguage.googleapis.com/v1beta/models/$(MODEL):generateContent

.PHONY: all clean

all: $(OUTPUT)

$(OUTPUT): $(PROMPT)
	@test -n "$$GEMINI_API_KEY" || (echo "GEMINI_API_KEY is not set" >&2; exit 1)
	jq -n --rawfile prompt $(PROMPT) '{contents: [{parts: [{text: $$prompt}]}]}' \
		| curl -sS "$(ENDPOINT)" \
			-H "x-goog-api-key: $$GEMINI_API_KEY" \
			-H "Content-Type: application/json" \
			-d @- \
		> $@

clean:
	rm -f $(OUTPUT)

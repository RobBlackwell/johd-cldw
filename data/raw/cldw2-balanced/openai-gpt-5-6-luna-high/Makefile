MODEL   := openai/gpt-5.6-luna
PROMPT  := ../prompt.txt
OUTPUT  := output.json
ENDPOINT := https://openrouter.ai/api/v1/chat/completions

TEXTS   := texts.jsonl

.PHONY: all clean

all: $(TEXTS)

$(OUTPUT): $(PROMPT)
	@test -n "$$OPENROUTER_API_KEY" || (echo "OPENROUTER_API_KEY is not set" >&2; exit 1)
	jq -n --arg model "$(MODEL)" --rawfile prompt $(PROMPT) '{model: $$model, messages: [{role: "user", content: $$prompt}], reasoning: {effort: "high"}}' \
		| curl -sS "$(ENDPOINT)" \
			-H "Authorization: Bearer $$OPENROUTER_API_KEY" \
			-H "Content-Type: application/json" \
			-d @- \
		> $@

$(TEXTS): $(OUTPUT)
	jq -r '.choices[0].message.content // error("no content: \(.error // .)")' $< > $@

clean:
	rm -f $(OUTPUT) $(TEXTS)

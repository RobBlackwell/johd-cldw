MODEL   := moonshotai/kimi-k3
PROMPT  := ../prompt.txt
OUTPUT  := output.json
ENDPOINT := https://openrouter.ai/api/v1/chat/completions

.PHONY: all clean

all: $(OUTPUT)

$(OUTPUT): $(PROMPT)
	@test -n "$$OPENROUTER_API_KEY" || (echo "OPENROUTER_API_KEY is not set" >&2; exit 1)
	jq -n --arg model $(MODEL) --rawfile prompt $(PROMPT) '{model: $$model, messages: [{role: "user", content: $$prompt}]}' \
		| curl -sS "$(ENDPOINT)" \
			-H "Authorization: Bearer $$OPENROUTER_API_KEY" \
			-H "Content-Type: application/json" \
			-d @- \
		> $@

clean:
	rm -f $(OUTPUT)

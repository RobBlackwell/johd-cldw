MODEL   := moonshotai/kimi-k3
# Pin inference to a single provider so results are reproducible across runs.
# allow_fallbacks: false makes OpenRouter 404 rather than silently reroute.
PROVIDER := moonshotai/mxfp4
PROMPT  := ../prompt.txt
OUTPUT  := output.json
ENDPOINT := https://openrouter.ai/api/v1/chat/completions

TEXTS   := texts.jsonl

.PHONY: all clean providers

all: $(TEXTS)

$(OUTPUT): $(PROMPT)
	@test -n "$$OPENROUTER_API_KEY" || (echo "OPENROUTER_API_KEY is not set" >&2; exit 1)
	jq -n --arg model "$(MODEL)" --arg provider "$(PROVIDER)" --rawfile prompt $(PROMPT) \
		'{model: $$model, provider: {order: [$$provider], allow_fallbacks: false}, messages: [{role: "user", content: $$prompt}]}' \
		| curl -sS "$(ENDPOINT)" \
			-H "Authorization: Bearer $$OPENROUTER_API_KEY" \
			-H "Content-Type: application/json" \
			-d @- \
		> $@

$(TEXTS): $(OUTPUT)
	jq -r '.choices[0].message.content' $< > $@

# List the provider slugs that actually serve $(MODEL), to check PROVIDER above.
providers:
	curl -sS "https://openrouter.ai/api/v1/models/$(MODEL)/endpoints" \
		| jq -r '.data.endpoints[].tag'

clean:
	rm -f $(OUTPUT) $(TEXTS)

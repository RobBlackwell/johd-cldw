MODEL   := qwen3:8b
PROMPT  := ../prompt.txt
OUTPUT  := output.json
ENDPOINT := http://localhost:11434/api/chat

.PHONY: all clean

all: $(OUTPUT)

$(OUTPUT): $(PROMPT)
	jq -n --arg model $(MODEL) --rawfile prompt $(PROMPT) '{model: $$model, messages: [{role: "user", content: $$prompt}], stream: false}' \
		| curl -sS "$(ENDPOINT)" \
			-H "Content-Type: application/json" \
			-d @- \
		> $@

clean:
	rm -f $(OUTPUT)

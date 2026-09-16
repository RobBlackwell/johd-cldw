MODEL   := qwen3:8b
PROMPT  := ../prompt.txt
OUTPUT  := output.json
TEXTS   := texts.jsonl
ENDPOINT := http://localhost:11434/api/chat

.PHONY: all clean

all: $(TEXTS)

$(OUTPUT): $(PROMPT)
	jq -n --arg model $(MODEL) --rawfile prompt $(PROMPT) '{model: $$model, messages: [{role: "user", content: $$prompt}], stream: false}' \
		| curl -sS "$(ENDPOINT)" \
			-H "Content-Type: application/json" \
			-d @- \
		> $@

$(TEXTS): $(OUTPUT)
	jq -r '.message.content' $< \
		| jq -R -c 'fromjson? | select(type=="object")' > $@

clean:
	rm -f $(OUTPUT) $(TEXTS)


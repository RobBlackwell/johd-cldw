TEXTS    := ../texts.jsonl
ERRORLOG := error.log

.PHONY: all clean

all: $(TEXTS)
	@rm -f $(ERRORLOG)
	@jq -c '.' $(TEXTS) | while IFS= read -r line; do \
		url=$$(printf '%s' "$$line" | jq -r '.download_url'); \
		title=$$(printf '%s' "$$line" | jq -r '.title'); \
		if [ -z "$$url" ] || [ "$$url" = "null" ]; then \
			echo "$$title: no download_url" >> $(ERRORLOG); \
			continue; \
		fi; \
		nofrag=$$(printf '%s' "$$url" | sed -e 's/#.*$$//'); \
		base=$$(printf '%s' "$$nofrag" | sed -e 's/?.*$$//' -e 's#.*/##'); \
		query=$$(printf '%s' "$$nofrag" | sed -n -e 's/^[^?]*?\(.*\)$$/\1/p'); \
		if [ -n "$$query" ]; then base="$${base}_$${query}"; fi; \
		fname=$$(printf '%s' "$$base" | sed -e 's/[^A-Za-z0-9._-]/_/g' -e 's/^\.*//'); \
		if [ -z "$$fname" ]; then \
			fname=$$(printf '%s' "$$url" | shasum -a 256 | cut -c1-16); \
		fi; \
		if [ -e "$$fname" ]; then \
			echo "Skipping (exists): $$fname"; \
			continue; \
		fi; \
		echo "Downloading: $$title -> $$fname"; \
		http_code=$$(curl -sS -L -w '%{http_code}' -o "$$fname.part" "$$url" 2>>$(ERRORLOG)); \
		curl_status=$$?; \
		if [ "$$curl_status" -ne 0 ]; then \
			echo "$$url: curl error (exit $$curl_status) [$$title]" >> $(ERRORLOG); \
			rm -f "$$fname.part"; \
		elif [ "$$http_code" -lt 200 ] || [ "$$http_code" -ge 400 ]; then \
			echo "$$url: HTTP $$http_code [$$title]" >> $(ERRORLOG); \
			rm -f "$$fname.part"; \
		else \
			mv "$$fname.part" "$$fname"; \
			if grep -qiE '^#REDIRECT' "$$fname"; then \
				echo "$$url: content is a redirect stub, not full text [$$title]" >> $(ERRORLOG); \
			elif grep -qiE '\{\{disambiguation\}\}' "$$fname"; then \
				echo "$$url: content is a disambiguation page, not full text [$$title]" >> $(ERRORLOG); \
			elif grep -qiE '\{\{versions' "$$fname"; then \
				echo "$$url: content is a versions/index page, not full text [$$title]" >> $(ERRORLOG); \
			fi; \
		fi; \
		sleep 1; \
	done
	@if [ -s $(ERRORLOG) ]; then \
		echo "Completed with errors, see $(ERRORLOG)"; \
	else \
		echo "All downloads completed successfully"; \
	fi

clean:
	find . -maxdepth 1 -type f ! -name Makefile -delete

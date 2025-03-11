markitdown:
	for file in ./docs/*.pdf; do \
		filename=$$(basename $$file .pdf); \
		uvx markitdown $$file -o "./docs/$$filename.md"; \
	done


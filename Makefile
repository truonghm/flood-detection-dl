markitdown:
	for file in ./ref/*.pdf; do \
		filename=$$(basename $$file .pdf); \
		uvx markitdown $$file -o "./ref/$$filename.md"; \
	done

bib4llm:
	uvx bib4llm convert ref

normalize-pdf-names:
	./scripts/normalize_pdf_names.sh

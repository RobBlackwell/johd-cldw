# Regenerate the outputs in reports/ that appear in the paper.
#
#   make sync      install dependencies into .venv (uv)
#   make reports   rebuild the figure and the generated tables
#   make clean     remove generated outputs

FIGDIR = reports/figures
TABDIR = reports/tables

# Run the scripts inside the project environment created by `make sync`.
# Override for a plain virtualenv, e.g.  make reports PYTHON=../.venv/bin/python
PYTHON = uv run python

sync:
	uv sync

reports: $(FIGDIR)/corpus_year_distributions.pdf \
         $(TABDIR)/gender_balance_table.tex \
         $(TABDIR)/genre_balance_table.tex \
         $(TABDIR)/corpus_table.tex

# Figure 1: year-distribution strip plot for the three corpora.
$(FIGDIR)/corpus_year_distributions.pdf: src/plot_year_distributions.py
	cd src && $(PYTHON) plot_year_distributions.py ../$@

# Table 1: author gender balance.
$(TABDIR)/gender_balance_table.tex: src/print_gender_ratios.py
	cd src && $(PYTHON) print_gender_ratios.py --latex-output ../$@

# Table 2: genre balance.
$(TABDIR)/genre_balance_table.tex: src/print_genre_distributions.py
	cd src && $(PYTHON) print_genre_distributions.py --latex-output ../$@

# Full CLDW2 text listing (supplementary; not included in the paper body).
$(TABDIR)/corpus_table.tex: src/make_corpus_table.py
	cd src && $(PYTHON) make_corpus_table.py --output ../$@

clean:
	rm -f $(FIGDIR)/corpus_year_distributions.pdf \
	      $(TABDIR)/gender_balance_table.tex \
	      $(TABDIR)/genre_balance_table.tex \
	      $(TABDIR)/corpus_table.tex

.PHONY: sync reports clean

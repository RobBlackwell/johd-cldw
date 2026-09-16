# Can AI Build (Better) Literary Corpora?

Data and code accompanying Blackwell, R.E., Taylor, J.E., Rayson, P.,
Gregory, I., Ezeani, I. and Cohn, A.G., 2026. *Can AI Build (Better)
Literary Corpora? Preliminary lessons from the Corpus of Lake District
Writing*. Submitted to the *Journal of Open Humanities Data*.



The paper uses the **Corpus of Lake District Writing (CLDW)** — 80 texts about the English
Lake District composed between c.1600 and 1900, manually curated at Lancaster
University (UCREL) and available at
<https://github.com/UCREL/LakeDistrictCorpus>. 

This repository holds the prompts, raw model responses and analysis
scripts behind the figures and tables used in the paper, released so
that results can be inspected and re-used.

## The two experiments reported in the paper

| Experiment | Directory | What it did |
| --- | --- | --- |
| ***Universe*** | `data/raw/cldw-universe/` | Given the original CLDW as examples, find every further Lake District text available in online repositories. Yielded **316 texts**. Claude Code 2.1.224 with **Opus 5**, run interactively; `TRANSCRIPT.md` is the full session log. |
| ***CLDW2*** | `data/raw/cldw2/claude-code/` | Without reference to the original, build an alternative 80-text corpus. Yielded **80 texts**, 13 shared with the CLDW. Claude Code 2.1.206 with **Sonnet 5** (`claude-sonnet-5`, as recorded in `output.json`), run headless via `claude -p`; see the stage `Makefile`. |

The other stages under `data/raw/` are supporting analyses: a follow-up on how
the agent chose its editions, and critiques of the *original* CLDW's own gender and genre balance.


## Reproducing the paper's outputs

```sh
make sync      # install dependencies (uv)
make reports   # rebuild the figure and tables
```

| Paper output | Generated file | Script |
| --- | --- | --- |
| Figure 1 (year distributions) | `reports/figures/corpus_year_distributions.pdf` | `src/plot_year_distributions.py` |
| Table 1 (gender balance) | `reports/tables/gender_balance_table.tex` | `src/print_gender_ratios.py` |
| Table 2 (genre balance) | `reports/tables/genre_balance_table.tex` | `src/print_genre_distributions.py` |
| Full CLDW2 listing (supplementary) | `reports/tables/corpus_table.tex` | `src/make_corpus_table.py` |

All four read only three inputs: `data/interim/ld80-metadata/ld80-metadata.jsonl`
(the original CLDW), `data/raw/cldw2/claude-code/texts.jsonl` (*CLDW2*) and
`data/raw/cldw-universe/texts.jsonl` (*universe*).

## Layout

```
data/
  external/
    LD80_transcribed/       The 80 original CLDW texts, standardised as UTF-8
    ld80-description/       Prose description of the original CLDW
  interim/
    ld80-metadata/          Original CLDW metadata, converted from CSV to JSONL
  raw/                      One subdirectory per experiment stage (see below)
src/                        Analysis scripts (run from src/), including
                            compare_metadata.py, which fuzzy-matches two
                            corpora by title and author
bin/
  render.py                 Jinja template renderer used by the stage Makefiles
  ensure-utf-8.sh           Normalises source texts to UTF-8
reports/
  figures/                  Figure PDFs
  tables/                   Generated LaTeX tables
```

Most stages under `data/raw/` have their own `Makefile`, which renders
`prompt.txt` from `prompt.txt.jinja` and runs the model. 

### Experiment stages

| Directory | Stage |
| --- | --- |
| `cldw2/` | Build an 80-text corpus from scratch (***CLDW2***, reported in the paper). Also holds the preliminary runs of the same prompt against other models — Gemini 3.1 Pro Preview (25 texts), GitHub Copilot CLI with `--model auto` (19), Qwen3-8B (20), Kimi-K3 (returned nothing usable; no `texts.jsonl`), plus two runs pasted by hand into Microsoft Copilot — M365 Copilot in Teams (20) and Copilot basic (15), each with a `README.txt` recording the date. None approached 80. |
| `cldw-universe/` | Exhaustive search for all available Lake District texts (***universe***, reported in the paper). |
| `why-editions/` | Follow-up asking the model to explain its edition choices; quoted in §3.2. Claude Code 2.1.224 with **Opus 5**, run interactively; `TRANSCRIPT.md` is the session log. Note this is a *different* model from the Sonnet 5 run whose choices it is explaining. |
| `gender-critique/`, `genre-critique/` | Give a model the *original* CLDW metadata and ask it to report on gender / genre balance — a check on what a model "sees" in the gold corpus. Run against Claude Sonnet 5, Claude Opus 4.8, Gemini 3.1 Pro Preview, Kimi-K3, Qwen3-8B and Copilot, one subdirectory each. `genre-critique/gold/` holds the reference breakdown. |
| `genre-critique-nometadata/` | The genre critique with the CLDW's metadata withheld: the model is given only each text's ID, author and title, so its genre labels come from prior knowledge of the works rather than from the corpus's own fields. Gemini 3.1 Pro Preview only. |

## Data format

We use the JSON object per line (JSONL) format throughout. For example:

```json
{
  "title":        "The English Lakes",
  "author":       "W. T. Palmer",
  "gender":       "M",
  "genre":        "Guide",
  "year":         1906,
  "repository":   "Project Gutenberg",
  "download_url": "https://www.gutenberg.org/cache/epub/57664/pg57664.txt",
  "reason":       "Victorian walking guide covering major Lake District valleys and peaks"
}
```

### A note on the downloaded texts

The full texts the agents downloaded are **not** included here: they are
public-domain scans from Project Gutenberg and the Internet Archive, reachable
from the `download_url` in the *CLDW2* stage's `texts.jsonl` files (the
*universe* records carry no URLs). The three model directories that
actually fetched texts — `cldw2/claude-code/`, `cldw2/gemini-3.1-pro-preview-high/`
and `cldw2/qwen3-8b/` — each keep a `downloads/Makefile`, which will refetch
them, and a `downloads/error.log` recording what failed. As the paper discusses,
OCR quality in these scans is sometimes poor.

## Licence

The code — the scripts in `src/` and `bin/`, and the Makefiles — is free software
under the [GNU General Public Licence v3 or later](https://www.gnu.org/licenses/gpl-3.0.html);
the full text is in [`LICENSE-GPL-3.0.txt`](LICENSE-GPL-3.0.txt).

Everything else — the prompts, the model responses, and the generated figures and
tables — is, like the original Corpus of Lake District Writing, licensed under a
Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License
[CC BY-NC-SA 4.0](http://creativecommons.org/licenses/by-nc-sa/4.0/).

Full terms are in [`LICENSE`](LICENSE).

## References

Rayson, P., Reinhold, A., Butler, J., Donaldson, C. E., Gregory, I. N., &
Taylor, J. E. (2017). A deeply annotated testbed for geographical text analysis:
The Corpus of Lake District Writing. <https://doi.org/10.1145/3149858.3149865>, **UCREL/LakeDistrictCorpus** — <https://github.com/UCREL/LakeDistrictCorpus>.

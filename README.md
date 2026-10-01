# Can AI Build (Better) Literary Corpora?

Data and code accompanying Blackwell, R.E., Taylor, J.E., Rayson, P.,
Gregory, I., Ezeani, I. and Cohn, A.G., 2026. *Can AI Build (Better)
Literary Corpora? Preliminary lessons from the Corpus of Lake District
Writing*. Submitted to the *Journal of Open Humanities Data*.

The paper uses the **Corpus of Lake District Writing (CLDW)** — 80
texts about the English Lake District composed between c.1600 and
1900, manually curated at Lancaster University (UCREL) and available
at <https://github.com/UCREL/LakeDistrictCorpus>.

This repository holds the prompts, raw model responses and analysis
scripts used for the paper, released so that results can be inspected
and re-used.

## Experiments

The experiments live in [`data/raw`](data/raw), one directory per
experiment, each holding the prompt (`prompt.txt`, rendered from
`prompt.txt.jinja` by `make`) and one sub-directory per model run with
that run's output — `texts.jsonl` for the corpus a run produced,
`trace.jsonl` for the Claude Code runs, and `output.json`, `output.md`
or `output.txt` for the single-shot API and chat runs.

Two experiments ask a model to *build* a corpus, in a balanced and an
unbalanced variant that differ by a single instruction: the balanced
prompt asks for diverse authors, gender balance and a good balance of
genres, the unbalanced one asks only that the selection be
representative of the period. The difference between the two is the
effect of that instruction.

- [`cldw2-balanced`](data/raw/cldw2-balanced) /
  [`cldw2-unbalanced`](data/raw/cldw2-unbalanced) — rebuild the CLDW
  from scratch: 80 Lake District texts composed between 1622 and 1900,
  each with a real, directly downloadable full text.
- [`universe-balanced`](data/raw/universe-balanced) /
  [`universe-unbalanced`](data/raw/universe-unbalanced) — given the 80
  texts already in the CLDW, find as many further candidates as
  possible (ideally several hundred), with no duplication and no
  download links required. `universe-balanced` was run twice
  (`claude-code`, `claude-code-run2`) to gauge run-to-run variation.

Two more ask a model to *critique* the existing corpus, from the LD80
description and metadata alone:

- [`gender-critique`](data/raw/gender-critique) — count the male and
  female authors in the CLDW.
- [`genre-critique`](data/raw/genre-critique) — tabulate the texts by
  genre and comment on how even the distribution is. The
  [`gold`](data/raw/genre-critique/gold) directory holds the answer
  computed directly from the metadata, for comparison with the model
  responses.

[`data/raw/prompt`](data/raw/prompt) holds the shared base template the
per-experiment prompts extend. 

[`data/interim/union/union.txt`](data/interim/union/union.txt) pools
every distinct work across the original CLDW and the model runs, one
row each with its gender and genre and a tick per corpus that holds it;
[`data/interim/female/female.txt`](data/interim/female/female.txt) is
the same table restricted to the female-authored texts.
[`data/interim/ub/ub.txt`](data/interim/ub/ub.txt) compares the two
`universe-balanced` runs against each other -- the one experiment
repeated under identical conditions -- and counts the works they found
in common, as a measure of run-to-run variation.

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

Rayson, P., Reinhold, A., Butler, J., Donaldson, C. E., Gregory,
I. N., & Taylor, J. E. (2017). A deeply annotated testbed for
geographical text analysis: The Corpus of Lake District
Writing. <https://doi.org/10.1145/3149858.3149865>,
**UCREL/LakeDistrictCorpus** —
<https://github.com/UCREL/LakeDistrictCorpus>.

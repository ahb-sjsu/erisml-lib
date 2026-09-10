# Geometric Series — proofreading and machine-validation protocol

This is the standard every volume follows for its proofreading pass and for
the **Machine Validation Record** appendix. It exists so the thirteen volumes
are checked the same way and report it the same way.

## 1. Scope of a pass

A pass covers every source file the volume's build renders (chapters, parts,
appendices, front/back matter). It has four stages, in order:

1. **Mechanical checks** — `python .build/series_check.py --run-code`
   (add `--check-links` when network is available). Fix every *hard* defect at
   the source. Triage every *candidate*; fix the real ones, ignore the rest,
   and never "fix" domain vocabulary or deliberate style.
2. **Read-through proofreading** — read every chapter in full. Fix at the
   source: spelling, grammar, agreement, punctuation, duplicated or dropped
   words, inconsistent terminology or notation across chapters, inconsistent
   heading formats (every chapter file's H1 is `# Chapter N: Title`; every
   appendix H1 is `# Appendix X: Title`), broken or wrong cross-references,
   numbering gaps, unfinished sentences, leftover drafting notes.
   **Do not change the argument, the claims, or the author's voice.** Where a
   claim looks wrong, record it (stage 4) instead of rewriting it.
3. **Machine verification of the mathematics and the numbers** — for every
   worked numerical example, stated identity, matrix/eigen computation,
   probability, or derivation step that can be recomputed, recompute it
   (sympy / numpy / scipy, or the book's own code). Run every fenced code
   block that is meant to be runnable; make the ones that fail run, or mark
   them explicitly as pseudocode in the text. Where the book cites a number
   from an experiment or dataset that lives in the repo, re-derive it from the
   repo artefact when that is feasible in minutes, otherwise record it as
   "not re-derived".
4. **Record** — write the appendix described in §2, rebuild, run the checker
   again (it must report zero hard defects), publish.

## 2. The Machine Validation Record appendix

One Markdown file per volume, placed with the other appendices and numbered as
the next free appendix letter (e.g. `appendix-e-machine-validation-record.md`).
H1: `# Appendix X: Machine Validation Record`. Sections, in this order:

1. **Scope and provenance** — date, source commit (short sha), tool versions
   (python, python-markdown, KaTeX, sympy/numpy), word and file counts, and
   the sentence "This appendix was produced by an automated proofreading and
   verification pass; it records what was checked and what was found, not an
   endorsement of the book's claims."
2. **Mechanical checks** — a table with one row per checker category:
   category · what it checks · items checked · defects found · defects fixed ·
   remaining. Include the KaTeX count (formulas parsed / failures), the
   cross-reference count (references checked / dangling), the code-block
   count (run / passing / failing / marked pseudocode).
3. **Proofreading changes** — grouped by kind (spelling, grammar, terminology,
   notation, structure, cross-references), each with a count and two or three
   representative before → after examples with chapter and section. Do not
   list every change; the git diff is the full record.
4. **Mathematical and numerical verification** — one entry per verified item:
   chapter/section · the claim as stated · how it was recomputed (a short code
   block or one-line method) · result (**Confirmed** / **Corrected** with the
   old and new value / **Discrepancy, not changed** with the reason / **Not
   re-derived**). Every discrepancy must appear here even if it was left in
   the text.
5. **Open items** — anything a human author must decide: suspect claims,
   citations that could not be located, figures referenced but missing, code
   that depends on unavailable data, style questions. Each with a location.
6. **Reproduction** — the exact commands to re-run the pass
   (`python .build/series_check.py --run-code`, the verification scripts, the
   build and publish commands). Verification scripts that are more than a few
   lines go in `.build/verify/` in the volume repo and are referenced here.

Keep it factual and compact: a reader should be able to tell in one page what
was checked, what changed, and what is still uncertain.

## 3. Publishing a pass

```bash
python .build/series_check.py --run-code       # 0 hard defects required
python .build/build.py                         # local build must succeed
git add -A <source files> .build/verify        # commit source + scripts + appendix on the default branch
git commit && git push
python .build/publish_site.py -m "site: proofreading + machine-validation pass" --push
```

Then in erisml-lib: `python tools/series-build/bump_submodules.py --commit && git push`.

## 4. Rules

- Edit **sources** (Markdown, or the docx for Geometric Ethics), never the built HTML.
- One volume per pass; do not touch other volume repos or erisml-lib except to re-pin.
- Do not remove or rename source files (URLs are public); add the appendix only.
- If `books.json` disagrees with the build config, stop and report; do not renumber.
- Leave untracked files you did not create alone (authors keep drafts in the tree).

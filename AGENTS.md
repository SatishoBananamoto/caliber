# AGENTS.md — caliber

**Start here: read `NORTHSTAR.md` in full before any work.** It is the
operating directive for this repo: mission, verified defect list, phase plan
with acceptance gates, formulas, process rules, and handoff format.

Quick constraints (duplicated from NORTHSTAR §4 because they are absolute):

- Work on branch `northstar`. Never push. Never publish to PyPI. Never touch
  `master`.
- No new runtime dependencies (stdlib only). `hypothesis` allowed as dev dep.
- No LLM calls in the package. No aggregate integrity score. No network in
  core paths.
- Full test suite (`python3 -m pytest -q`) green before any chunk is "done".
- Never `rm` project files — `git mv` to `archive/` instead.
- Append learnings to `lab/NOTEBOOK.md`; update `GAUGE.md` at phase gates.

Tracking doc: `GAUGE.md`. External review that grounded the directive:
`REVIEW.md` (grade + gaps) and NORTHSTAR §2 (verified defects with locations).

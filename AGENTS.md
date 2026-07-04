# AGENTS.md — caliber

**Start here: read `NORTHSTAR.md` in full before any work.** It is the
operating directive for this repo: mission, verified defect list, phase plan
with acceptance gates, formulas, process rules, and handoff format.

Round two active directive: read `NORTHSTAR2.md`; its Phase A docs are
`docs/METHOD.md` and `docs/SPEC.md`.

Quick constraints (duplicated from NORTHSTAR §4 because they are absolute):

- Work only on the active round branch (`northstar2` as recorded in
  GAUGE.md's latest entry — check there, it is the source of truth). Never
  push. Never publish to PyPI. Never touch `master`.
- No new runtime dependencies (stdlib only). `hypothesis` allowed as dev dep.
- No LLM calls in the package. No aggregate integrity score. No network in
  core paths.
- Full test suite (`python3 -m pytest -q`) green before any chunk is "done".
- Never `rm` project files — `git mv` to `archive/` instead.
- Append learnings to `lab/NOTEBOOK.md`; update `GAUGE.md` at phase gates.

Tracking doc: `GAUGE.md`. External review that grounded the directive:
`REVIEW.md` (grade + gaps) and NORTHSTAR §2 (verified defects with locations).

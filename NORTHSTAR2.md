# NORTHSTAR2.md — Caliber Round Two: Citable, Specifiable, Externally Verifiable

> Directive for the second autonomous run. Self-contained, but READ FIRST:
> `NORTHSTAR.md` (round-one directive — its §4 constraints, §6 operating loop,
> §7 notebook rules, and §8 subagent rules apply verbatim here) and
> `lab/HANDOFF.md` (round-one results and ranked gaps).
> Written 2026-07-04, after round one completed at commit `e127398`.

---

## 0. Mission

Round one made caliber statistically rigorous, adversarially benchmarked, and
tamper-evident (30 commits, 143→202 tests, phases 0–4 gated). Round two turns
it into three things it is not yet:

1. **Citable** — `docs/METHOD.md`: the written method + benchmark paper.
   Prior-art research (2026-07-04, sources in §5) shows the gaming-forensics
   niche is theoretically known but operationally unoccupied. This document
   stakes the claim: *the first tool that stress-tests an agent's calibration
   record against known gaming strategies, with measured detection operating
   points.*
2. **Specifiable** — `docs/SPEC.md`: a normative format spec precise enough
   that a stranger could write a second implementation of `verify-log` and
   `verify-card` without reading caliber's source. Only after this exists is
   any "protocol" language honest.
3. **Externally verifiable** — signed cards and third-party outcome
   adjudication (Phase B, gated; see §2). Round one's biggest remaining
   honesty gap (HANDOFF gap #3) is that the agent still grades its own
   homework. Adjudication hooks are the first structural fix.

The self-check sentence, unchanged from round one: **"Am I making the card
more honest, or just more complex?"**

---

## 1. Branch and review-isolation rules

- Round one (`northstar` branch) is **awaiting Satish's review**. Do not
  rewrite its history and do not churn files he is reviewing.
- Work on a new branch: `git checkout -b northstar2 northstar`.
- Commit format: `northstar2(<phase><item>): <what> — <evidence>`.
- Continue `lab/NOTEBOOK.md` (same file, EXP numbering continues from where
  round one ended).
- Allowed edits to round-one deliverables are listed exhaustively in A3.
  Everything else under review is read-only this round.

## 2. Phase gating — HARD RULE

**Phase A may run immediately. Phases B and C are BLOCKED** until Satish
records his round-one sign-offs. The marker is a GAUGE.md entry containing
the string `R1-SIGNOFF` (Satish writes it, not you). Before starting Phase B:

```bash
grep -n "R1-SIGNOFF" GAUGE.md
```

If absent: stop after the Phase A gate, write the handoff (§7), end the run.
Do not interpret anything else as permission.

---

## 3. Phase A — Citable and specifiable (docs only, no behavior changes)

### A1. `docs/METHOD.md` — the method paper (the core of this run)

Audience: a technically literate stranger from the agent-evals or forecasting
community. Tone rules are binding:

- Every quantitative claim must be traceable to a number in this repo
  (`lab/REPORT.md`, `lab/results/*.json`, test files) or to a citation in §5.
- No marketing language. Where caliber cannot do something, say so in the
  main text, not a footnote — the smart-fabricator impossibility boundary and
  the self-adjudication limitation are *features of the paper*, not
  embarrassments.
- Cite ONLY from §5 sources or classics you can verify. If network access
  fails, cite conservatively from the descriptions given here. Never invent
  a citation, page number, or result.

Required structure:

1. **Problem.** Agents state confidence; nothing grounds it. Track records
   are self-reported and gameable. Two distinct failure modes: honest
   miscalibration, and adversarial record-inflation.
2. **Related work** (from §5): human calibration journals (PredictionBook,
   Fatebook) — mature but human-oriented and gaming-naive; agent-calibration
   research (HTC/GAC, TrustBench) — in-the-moment estimators, not
   longitudinal ledgers; reliability scoring (BayesTruth) — outcome-based
   tool reliability, not stated-confidence honesty; calibeating theory
   (Foster–Hart line) — proves calibration alone is gameable, prescribes
   resolution — theory without tooling. Position caliber in the empty cell
   of that matrix.
3. **The instrument.** Estimator choices and why: mean-stated-confidence
   bucket gaps (not midpoints), Wilson intervals, exact binomial tests,
   Spiegelhalter's Z, equal-mass adaptive buckets, Brier + Murphy
   decomposition. One paragraph each, with the failure mode the naive
   alternative causes (round one's D1/D2 defects make good examples —
   caliber's own flagship card once showed a "strength zone" built on 4
   predictions; tell that story, it demonstrates the honesty standard).
4. **The adversarial benchmark.** Population zoo (honest, shifted, noisy,
   farmer, patient farmer, naive/smart fabricator, template spammer, domain
   camper, importer, mixtures), 500 replicates × n ∈ {20,50,100,300}, the
   FPR/power tables imported from `lab/REPORT.md`, and how thresholds were
   re-derived from measured operating points.
5. **Threat model and impossibility boundary.** Distill `lab/THREATMODEL.md`:
   what record-only analysis detects (with measured power), what it cannot
   detect in principle (smart fabrication; semantic difficulty), and what
   evidence level fixes each (witnessed timing, anchored commitments,
   external adjudication).
6. **Limitations.** Lead with self-adjudication: outcomes are recorded by
   the same party that predicted. Then: unwitnessed imports, manual
   anchoring, single-agent scope, binary outcomes only.
7. **Reproduction.** Exact commands: install, run bench, regenerate tables,
   run the tamper tests. A reader must be able to reproduce every table.

### A2. `docs/SPEC.md` — record and verification spec (v0.1)

Normative, RFC-flavored ("MUST/SHOULD"), versioned `spec_version: 0.1`.
Covers exactly what exists today — do not spec unbuilt features:

1. Prediction record fields, types, and constraints (confidence ∈ [0.50, 0.99]).
2. Event log: event types, canonical JSON serialization, the hash-chain rule
   (what exactly is hashed, encoding, `prev_hash` linkage, genesis).
3. Commitment: hash construction, salt, what an unanchored vs anchored
   commitment proves (from `caliber/commitment.py` docstring).
4. Anchor format and semantics.
5. Card: field-by-field, including every statistic and its formula.
6. Verification algorithms: `verify-log` and `verify-card` as step-by-step
   pseudocode a second implementation could follow.
7. **Golden test vectors**: add `tests/vectors/` with (a) a small valid event
   log + its expected head hash, (b) a tampered variant + the expected
   failure, (c) a card JSON + the store that produces it. Wire a test that
   validates the vectors, so the spec is executable, not aspirational.

### A3. Round-one leftovers (exhaustive list of permitted edits)

- `CLAUDE.md`: first lines still say "Trust protocol for AI agents" — align
  with the round-one repositioning ("Calibration instrument…"). Touch only
  the identity wording, not the history sections.
- `AGENTS.md`: add one line pointing to `NORTHSTAR2.md` as the active
  directive and `docs/SPEC.md` + `docs/METHOD.md` when they exist.
- `README.md`: at most, add two links (METHOD, SPEC) to the existing docs
  section. No other README changes this round.

### Phase A gate (binding)

- METHOD.md claims audit: grep every number in the document and match it to
  its source file; record the audit as a notebook EXP entry.
- SPEC.md executability: the golden-vector test passes; a notebook entry
  demonstrates recomputing the vector head hash with a ~20-line standalone
  script that imports nothing from `caliber/` (proving spec sufficiency).
- Full suite green; `python3 -m compileall -q caliber` clean.
- GAUGE.md phase entry written.

---

## 4. Phase B — Externally verifiable (BLOCKED until R1-SIGNOFF, see §2)

### B1. Signed cards

- Core stays zero-runtime-dependency. Signing ships as an **optional extra**:
  `caliber-trust[signing]`, using the `cryptography` package (Ed25519). The
  deviation from the zero-dep rule is explicit and opt-in; document it.
- `caliber keygen` (stores keypair under the store dir, private key 0600),
  `caliber card --sign`, `caliber verify-card --pubkey <file>`.
- Signature covers the canonical card JSON plus the event-log head hash, so
  a signed card binds to a specific log state.
- Tests: valid signature verifies; any single-byte mutation fails; unsigned
  cards still work everywhere.

### B2. External adjudication

The first structural fix for self-grading. Design:

- New event type `adjudicated`: records outcome, adjudicator identity string,
  optional adjudicator signature, and free-text evidence note.
- `caliber adjudicate <prediction-id> --correct/--incorrect --by <identity>`.
- Cards split accuracy into `self_verified` vs `adjudicated` sections with
  separate counts and Wilson intervals — never blended into one number.
- Integrity: adjudicated share becomes a reported metric (not a flag).
- Spec bump to v0.2 covering the new event and card fields.

### B3. Anchoring hardening

- `caliber anchor --emit <file>`: append the head to a separate anchors file
  suitable for committing to git or posting anywhere public; document the
  git-commit pattern in GETTING_STARTED.
- Optional adapters may be sketched in docs but NOT implemented with new
  network dependencies this round.

### Phase B gate

Forged signed card fails verification; adjudicated vs self-verified split
visible in card JSON and summary; spec v0.2 golden vectors added; suite green;
GAUGE entry.

---

## 5. Prior-art sources for METHOD.md (verified 2026-07-04)

Human prediction journals:
- Fatebook (Sage, open source): https://fatebook.io/ and
  https://www.lesswrong.com/posts/yS3d46m23wRKDQobt/introducing-fatebook-the-fastest-way-to-make-and-track
- PredictionBook (~2009, predecessor): https://www.lesswrong.com/posts/ofSYgmMby7iqxJqi6/predictionbook-com-track-your-calibration

Agent-calibration research (estimators, not ledgers; no released tooling found):
- "Agentic Confidence Calibration" (HTC + General Agent Calibrator):
  https://arxiv.org/pdf/2601.15778
- TrustBench (stated-confidence → trust via isotonic regression):
  https://arxiv.org/pdf/2603.09157

Adjacent tooling (same month, different primitive):
- BayesTruth — Beta-Bernoulli reliability scores for tools/MCP servers with a
  SHA-256 hash-chained audit trail; tracks call success, not stated-confidence
  honesty: https://github.com/davccavalcante/bayestruth
- mcp-confidence — logprob-based accept/verify/escalate gate:
  https://github.com/shaxzodbek-uzb/mcp-confidence

Gaming theory (known theory, no operational tool found):
- "Calibeating" (Foster & Hart) — calibration is gameable to arbitrary
  perfection: https://arxiv.org/pdf/2209.04892
- Forecast hedging: https://simons.berkeley.edu/talks/forecast-hedging-calibration-game-equilibria

Classics for estimator citations: Brier 1950; Murphy 1973 (decomposition);
Wilson 1927 (interval); Spiegelhalter 1986 (Z test); Gneiting & Raftery 2007
(proper scoring rules): https://sites.stat.washington.edu/raftery/Research/PDF/Gneiting2007jrssb.pdf

---

## 6. Constraints (inherited + this round)

All of NORTHSTAR.md §4 remains binding: never push, never publish, no LLM
calls in the package, no aggregate integrity score, no network in core paths,
full suite green per chunk, never `rm` (archive instead). Additions:

- No new **required** runtime dependencies. `cryptography` only as the
  opt-in `[signing]` extra, only in Phase B.
- Do not modify `caliber/integrity.py` thresholds this round — they carry
  measured operating points; METHOD.md documents them, nothing retunes them.
- Do not start Phase B without the `R1-SIGNOFF` marker (§2). Phase C
  (succession gates, from the AgentOS design) is explicitly OUT of this run —
  it gets its own directive after adjudication exists.

## 7. Definition of done

Phase A gate passed (and Phase B only if unblocked and gated). Then append to
`lab/HANDOFF.md`: a dated "Round Two" section with what shipped, the METHOD.md
claims-audit result, spec version state, engram-worthy learnings, decisions
needing Satish, and remaining gaps re-ranked. Working tree clean, everything
committed on `northstar2`, nothing pushed, nothing published.

Honesty of the handoff outranks completeness of the work — same as round one.

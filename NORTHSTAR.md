# NORTHSTAR.md — Caliber World-Class Directive

> Operating directive for a long-running autonomous coding session (Codex).
> Self-contained: assume no other context. Read fully before writing any code.
> Written 2026-07-04, grounded in an external code review of commit `ab54e5b`.

---

## 0. Mission

Caliber today is a good calibration journal with unusually thoughtful gaming
detection. The mission of this run is to make it **the reference instrument for
measuring, stress-testing, and proving AI agent calibration**.

"World-class" is not a feeling. It is four testable properties:

1. **Rigorous** — every number on a Trust Card has a defensible estimator and
   uncertainty quantification. A forecasting researcher reading the card format
   should find nothing to object to.
2. **Adversarially validated** — every integrity flag has a *measured* false
   positive rate and detection power against a published attacker simulation
   suite. No hand-set threshold survives unless the lab data justifies it.
3. **Verifiable** — a third party can detect tampering or fabrication in a
   prediction record they did not witness being made. Today they cannot.
4. **Adoptable** — a stranger goes from `pip install caliber-trust` to their
   first honest Trust Card in under 5 minutes, and the README never claims more
   than the code delivers.

The single sentence to re-read whenever lost:
**"Am I making the card more honest, or just more complex?"** If a change does
not increase honesty (rigor, robustness, verifiability) or adoption, drop it.

---

## 1. Current state (verified 2026-07-04)

- Local repo `~/caliber`, branch `master`, in sync with
  `github.com/SatishoBananamoto/caliber` at `ab54e5b`. Branch
  `integrity-metrics` is fully merged — delete it, don't re-reconcile.
- v0.2.0 published on PyPI as `caliber-trust`. 143 tests, all passing
  (`python3 -m pytest -q`). CI green. Pure stdlib runtime — zero dependencies.
  This is a load-bearing feature; keep it.
- Modules: `tracker.py` (predict/verify loop), `card.py` (Trust Card + buckets),
  `integrity.py` (Murphy decomposition + 7 advisory flags — the crown jewel),
  `commitment.py` (SHA256 commit-reveal), `storage.py` (whole-file JSON
  save/load), `trajectory.py`, `importer.py`, `cli.py`, `mcp_server.py`.
- Real corpora available for empirical checks: the `default` store (live use)
  and the imported CALIBRATE corpus (~94 verified predictions), plus
  `trust-card-claude-opus.json` (77-prediction flagship card in the README).
- Tracking doc: `GAUGE.md` (session log + work items). Keep it updated — see §7.
- `docs/` contains untracked explainer files; leave them alone.

---

## 2. Verified defects — fix these, they are not hypotheses

Each was confirmed by reading/running the code. Cite the evidence in commits.

**D1. Insufficient data makes zone-flagging EASIER (card.py ~line 201-215).**
A bucket becomes a danger/strength zone when `gap > 0.10 AND (significant is
True OR significant is None)`. `None` means n < 5 — too small to test. So a
bucket with 3-4 predictions is flagged *because* it can't be tested. This is
backwards, and it produced the embarrassing `"strength_zones": ["50-59"]` from
4 predictions in the README's flagship card. Fix: a zone may only be flagged
when the test ran AND is significant. Regenerate the flagship card after.

**D2. Card and integrity disagree on "expected accuracy".**
`card.py` compares bucket accuracy against the *bucket midpoint*
(`expected_accuracy` property); `integrity.py`'s Mendel test correctly uses the
*mean stated confidence within the bucket*. Midpoint comparison injects up to
±5pp of pure binning bias into every calibration_gap. Standardize on mean
stated confidence everywhere. This changes reported gaps — note it in the
CHANGELOG as a correction, with before/after on the real corpora.

**D3. No uncertainty on bucket accuracy.**
Bucket accuracies are reported as point estimates. Add Wilson score intervals
(formula in §5). The card JSON should carry `ci95: [lo, hi]` per bucket; the
human summary should render them.

**D4. Significance test is a normal approximation allowed at n≥5.**
At n=5 the normal approximation to the binomial is junk. Replace with the exact
binomial test (log-space, formula in §5). Pure stdlib, no scipy.

**D5. The commitment scheme proves nothing to a third party.**
`commitment.py` is sound cryptography stored in the wrong place: hash AND salt
live in the same mutable JSON file as the predictions. Anyone can regenerate
the whole store, commitments included, with any timestamps. Without an external
anchor the scheme is theater. Fix is Phase 3 (hash-chained log + anchoring),
plus an honest docstring/README statement of exactly what a commitment does and
does not prove at each anchoring level.

**D6. Storage is rewrite-the-world.**
`FileStorage.save()` rewrites the entire store on every mutation. No
append-only structure, no tamper evidence, and a crash mid-save can lose the
store. Phase 3 replaces the source of truth with an append-only JSONL event
log (hash-chained); the JSON snapshot becomes a derived cache.

**D7. Integrity thresholds are hand-set and unvalidated.**
Every constant at the top of `integrity.py` (0.60 top-bucket share, 0.09
uncertainty floor, 120s instant window, HHI 0.60, ...) was chosen by intuition.
Nobody knows the false-positive rate on honest agents or the detection power
against attackers. Phase 2 exists to measure and re-derive them.

**D8. Known evasions are documented but unaddressed.**
`tests/test_integrity_adversarial.py` already encodes two working attacks:
`test_patient_farmer_evades_latency_check` and
`test_synthetic_import_timestamps_evade_import_share`. These are honest tests
of dishonest gaps. Phase 2 must either close them or formally document them as
outside the threat model (with reasoning in THREATMODEL.md).

**D9. README overclaims.**
"Trust protocol for AI agents" — there is no protocol: no spec, no signing, no
external verification, no second implementation. It also links to
`github.com/SatishoBananamoto/my-universe`, which is **private** — a 404 for
every reader. Phase 4 repositions honestly.

---

## 3. Phase plan

Phases are sequential; gates are binding. Within a phase, chunks marked ∥ may
be parallelized across subagents (§8). Suggested budget in parentheses —
timeboxes, not targets.

### Phase 0 — Baseline (≤45 min)
1. Read `GAUGE.md`, `REVIEW.md`, every module in `caliber/`, and the two
   adversarial-evasion tests. Delete the merged `integrity-metrics` branch.
2. Create working branch: `git checkout -b northstar`.
3. Run the full suite; record the count. Run `caliber card` and
   `caliber integrity` against the real corpora; save outputs verbatim into
   `lab/NOTEBOOK.md` under a `## BASELINE` heading (create `lab/` now).
4. **Gate:** tests green, baseline outputs recorded, notebook exists.

### Phase 1 — Statistical core (2-3 h)
1. Fix D1 (zone gating). Add a regression test: 4 predictions in one bucket
   with gap > 0.10 must NOT produce a zone.
2. Fix D2 (mean stated confidence as expectation, everywhere). Keep the field
   name `calibration_gap`; document the definition change.
3. Fix D3 (Wilson intervals on every bucket, in JSON and summary).
4. Fix D4 (exact binomial test). ∥
5. Add to the card: Brier score + its Murphy decomposition (already computed in
   integrity.py — surface it), and Spiegelhalter's Z (binning-free calibration
   test, formula in §5) as `calibration_z` with its two-sided p-value. ∥
6. Add adaptive (equal-mass) binning as a *second view*: report both the fixed
   5-bucket table (backward compatible) and `adaptive_buckets` (§5). Do not
   remove the fixed buckets — MCP/CLI consumers depend on them.
7. Property-based tests (add `hypothesis` as a DEV dependency only):
   - Murphy identity `brier == rel - res + unc` to 1e-9 on random streams.
   - Wilson interval: Monte Carlo coverage on a grid
     n ∈ {5,10,20,50,200} × p ∈ {0.55,0.7,0.85,0.95} — accept 93-97% empirical
     coverage for the 95% interval.
   - Exact binomial test: agreement with known values (e.g. two-sided
     p for k=9, n=10, p0=0.5 is ≈ 0.021484) to 1e-6.
8. Regenerate `trust-card-claude-opus.json` with the corrected statistics and
   update the README's embedded card and its interpretation paragraph.
9. **Gate:** all identities/coverage tests pass; regenerated flagship card
   contains no zone or claim that a skeptical statistician would strike.

### Phase 2 — The Adversarial Lab (3-5 h — the core of this run)
Build `lab/` at repo root (NOT inside the `caliber/` package; never shipped).

1. `lab/simulate.py` — generative models of prediction streams. Every simulator
   takes `(n, seed)` and returns `list[Prediction]`-compatible dicts. Required
   population zoo:
   - `honest(sharpness)` — draw true probability p from a Beta distribution
     (sharpness controls spread), stated confidence c = clip(p, .50, .99),
     outcome ~ Bernoulli(p). Latency ~ lognormal(median≈10 min).
   - `overconfident(delta)` / `underconfident(delta)` — c = clip(p + delta).
   - `noisy(sigma)` — c = clip(p + Normal(0, sigma)): poor discrimination.
   - `farmer(easy_share)` — fraction of stream has p≈0.98, c≥0.95, near-zero
     latency, template claims ("file N exists").
   - `patient_farmer(easy_share)` — same but latency > 120s (current evasion D8).
   - `naive_fabricator` — invents outcomes so each bucket's accuracy exactly
     matches its mean confidence (Mendel's target).
   - `smart_fabricator` — outcome ~ Bernoulli(c): statistically
     indistinguishable from honest by construction. Expected result: NOTHING
     catches it. That is a finding, not a failure — it defines the boundary
     where behavioral/witnessing evidence is the only recourse. Document it.
   - `template_spammer`, `domain_camper(k_domains=1)`,
     `bulk_importer(import_share)` — target the remaining flags.
   - `mixture(honest_frac, attacker, ...)` — realistic partial gaming.
2. `lab/run_bench.py` — for every (population × n ∈ {20, 50, 100, 300}) run
   ≥500 seeded replicates, compute per-flag firing rates. Emit
   `lab/results/bench-<git-sha>.json` and a Markdown table in
   `lab/REPORT.md`: honest populations → false positive rate per flag;
   attacker populations → detection power per flag. Deterministic seeds;
   runtime target < 5 min for the full bench (it's arithmetic, not I/O).
3. **Threshold re-derivation.** For each constant in `integrity.py`, choose the
   value that keeps honest FPR ≤ 5% (per flag, at n=50) while maximizing power
   against its target attacker. If the current hand-set value survives, keep it
   and record its measured operating point in a comment:
   `# FPR 2.1% honest@n=50, power 94% vs farmer@n=50 — lab bench <sha>`.
   Every constant gets such a comment. No exceptions.
4. Close or classify D8's two evasions:
   - Patient farmer: latency alone can't catch it — but farming leaves
     LOW_OUTCOME_VARIANCE + CONFIDENCE_CONCENTRATION signatures regardless of
     latency. Verify the combination catches it; if not, build what does.
   - Synthetic import timestamps: unfixable inside the store (attacker writes
     the file) — Phase 3's chain + anchoring is the real fix; document.
5. Encode the whole bench as regression tests: `tests/test_lab_bench.py` runs a
   small (fast) version — every attacker population must trip its expected
   flag(s) at n=100; every honest population must stay under the FPR budget.
6. `lab/THREATMODEL.md` — the honest boundary document: attacks detected (with
   measured power), attacks NOT detectable from the record alone
   (smart fabricator, timestamp forgery) and what evidence level fixes each
   (witnessed timing, anchored commitments, third-party adjudication).
7. **Gate:** REPORT.md has full FPR/power tables; every threshold constant
   carries a measured operating point; regression tests encode the bench;
   THREATMODEL.md states the impossibility boundary explicitly.

### Phase 3 — Tamper evidence (2-3 h)
1. New source of truth: append-only JSONL event log
   (`<store>/<agent>.events.jsonl`): events `predicted`, `verified`,
   `imported`, each carrying `prev_hash` = SHA256 of the previous line —
   a hash chain. The existing JSON file becomes a derived snapshot rebuilt
   from the log (keep it for backward compatibility of readers).
2. `caliber verify-log` — replay the chain; any edited/deleted/reordered
   historical line breaks verification. Test by mutating mid-chain bytes.
3. `caliber anchor` — print (and append as an event) the current chain head
   hash, suitable for pasting into a git commit, gist, or timestamping
   service. Optional adapters only; zero new runtime deps; no network calls
   in core paths.
4. `caliber verify-card <card.json>` — recompute every statistic on the card
   from the event log and fail on any mismatch (closes the roadmap's v0.2
   promise). Wire commitments into events so commit-reveal rides the chain.
5. Migration: `caliber migrate` converts an existing JSON store into a
   fresh-chain log, explicitly marked `origin: migrated` (an *unwitnessed*
   chain — integrity's UNWITNESSED_HISTORY reasoning applies; be honest).
6. Update `commitment.py` docstring and README: a commitment is only as strong
   as its anchor. Unanchored = self-attestation; anchored chain head = third
   parties can detect retroactive rewrites from that point forward.
7. **Gate:** tamper tests pass (any historical mutation detected); a card that
   disagrees with its log fails `verify-card`; migration round-trips the real
   corpora with identical card statistics.

### Phase 4 — Honest repositioning (1-2 h)
1. README rewrite. New identity line: "Calibration instrument for AI agents —
   measure it, stress-test it, prove it." Remove "trust protocol" until a spec
   exists. Remove/replace the dead `my-universe` link (private repo — 404).
   Add a Threat Model section distilled from `lab/THREATMODEL.md` — what a
   Trust Card proves at each evidence level. Keep the A2A/registry story as
   *motivation*, not as a claim of current capability.
2. Verify GETTING_STARTED.md end-to-end in a clean venv
   (`python3 -m venv /tmp/caliber-fresh && pip install -e .`); paste the
   transcript into the notebook. Fix every discrepancy found.
3. CHANGELOG.md entry for v0.3.0: statistical corrections (D1/D2 changed
   reported numbers — say so plainly), lab bench, hash-chained log,
   verify-card. Bump version in `pyproject.toml` and `__init__.py`.
   **Do NOT publish to PyPI. Do NOT push. Satish releases.**
4. **Gate:** fresh-venv transcript clean; README contains zero claims the code
   can't demonstrate; CHANGELOG written.

### Phase 5 — Stretch (only if all gates passed)
`docs/METHOD.md` — the citable method paper: estimator choices with reasoning,
the detection benchmark with tables from `lab/REPORT.md`, the threat model,
related work (Brier 1950; Murphy 1973 decomposition; Wilson 1927 interval;
Spiegelhalter 1986 Z; Gneiting & Raftery 2007 proper scoring rules; calibration
binning-bias literature; Tetlock's Good Judgment Project for the
forecasting-track-record precedent). This document is what makes caliber
world-class rather than merely good: it invites expert scrutiny in writing.

---

## 4. What NOT to do (binding)

- **No new runtime dependencies.** Pure stdlib is caliber's portability moat.
  `hypothesis` is allowed as a dev/test dependency only.
- **No aggregate integrity score.** A single number becomes the gaming target.
  This is a settled design decision (GAUGE.md); do not relitigate.
- **No LLM calls anywhere in the package.** Determinism is the product.
- **No blockchain, no external services in core paths.** Anchoring adapters
  are optional and offline-safe.
- **No breaking the MCP tool contracts** (`caliber_predict`, `caliber_verify`,
  `caliber_card`, `caliber_summary`, `caliber_list`, `caliber_trajectory`,
  `caliber_integrity`) — additive changes only, or version-note them.
- **Never `git push`. Never publish to PyPI. Never force-push.** Work stays on
  the `northstar` branch, local, for Satish's review.
- **Don't delete or rewrite GAUGE.md history** — append to it.
- **Don't move files into `archive/` deletions — never `rm` project files;**
  if something must go, `git mv` it into `archive/` with a note.
- **Don't gold-plate.** Rendering, dashboards, web UIs, multi-agent registries
  are all out of scope for this run.

---

## 5. Formulas (implement in pure stdlib; no scipy)

**Wilson 95% interval** for k successes in n trials, z = 1.959964:
```
p̂ = k/n
center = (p̂ + z²/(2n)) / (1 + z²/n)
half   = (z / (1 + z²/n)) · sqrt(p̂(1−p̂)/n + z²/(4n²))
CI = [max(0, center − half), min(1, center + half)]
```

**Exact binomial two-sided p-value** for k of n at null p0 — sum in log space:
```
ln pmf(i) = lgamma(n+1) − lgamma(i+1) − lgamma(n−i+1)
          + i·ln(p0) + (n−i)·ln(1−p0)
p_two = Σ over all i where pmf(i) ≤ pmf(k)·(1+1e−9) of pmf(i)
```
(`math.lgamma`; n here is bucket-sized — ≤ a few thousand — so O(n) is fine.)

**Spiegelhalter's Z** (binning-free miscalibration test) over verified
predictions with stated confidences f_i and outcomes o_i ∈ {0,1}:
```
Z = Σ(o_i − f_i) / sqrt(Σ f_i(1 − f_i))     p_two = 2·(1 − Φ(|Z|))
```
(Φ available via the existing `_norm_cdf` erfc trick.)

**Equal-mass (adaptive) bins:** sort verified predictions by confidence, cut
into ⌈n/25⌉ bins of (near-)equal count (minimum 3 bins); report per-bin mean
confidence, accuracy, Wilson CI. Sidesteps fixed-bucket binning bias.

**Debiased calibration error (report alongside raw):** for each bin subtract
the expected noise contribution `acc_k(1−acc_k)/n_k` from the squared gap
before aggregating; floor at 0.

---

## 6. Operating loop — how to work each chunk

This project runs on explicit process rules. They are binding.

1. **Plan first.** Before code: 3-6 bullet mini-plan in `lab/NOTEBOOK.md`.
2. **One chunk at a time.** A chunk = one coherent change (one defect, one
   simulator family, one CLI command). Implement → test → notebook → commit.
3. **Full suite after every chunk** (`python3 -m pytest -q`). A chunk is not
   done with red tests. Never claim results without command output.
4. **Commit at chunk boundaries** on the `northstar` branch. Message format:
   `northstar(P<phase>): <what> — <evidence, e.g. "162→171 tests">`.
5. **Update GAUGE.md at phase gates** (not every chunk): a dated entry under
   the session log — what shipped, what changed numerically, what's next.
6. **Read errors in full.** Fix the specific failure; no shotgun edits.
7. **Timeboxes:** a chunk stuck for ~90 minutes or 3 failed approaches gets a
   BLOCKED entry in the notebook (symptom, attempts, hypothesis) and you move
   to the next independent chunk. Return only with a new idea.
8. **Verify before assert:** all counts from commands (`pytest -q`, `wc -l`,
   `grep -c`), never from memory. Sizes as ranges.

---

## 7. Lab notebook & learning capture

`lab/NOTEBOOK.md` — append-only, timestamped. This substitutes for the engram
knowledge base (not available to this agent). Entry types:

- `EXP` — hypothesis → experiment → result → decision. Every bench run, every
  threshold change, every coverage simulation gets one.
- `DEC` — a design choice with reasoning and alternatives rejected.
- `LRN` — something discovered that changes future approach (e.g. "flag X
  false-positives on honest sharp agents at n=20 because …").
- `MST` — something that broke; root cause; prevention.
- `BLOCKED` — see §6.7.

The bar for LRN/MST/DEC: *would a future session make a worse decision without
this entry?* Findings that clear the bar get surfaced in the final handoff so
Satish can port them to engram.

**Meta-checkpoints** — at every phase gate, and any time work feels effortless
for a long stretch, answer in the notebook:
1. Re-read §0. Is the current chunk increasing honesty or just complexity?
2. What's the last thing I verified against reality (not against my own tests)?
3. Is any result too clean? (Caliber's own lesson: small samples lie, and
   suspiciously perfect data is the signature of self-deception.)
4. Am I answering the question that was asked, or a nearby easier one?

---

## 8. Subagent management (if the runner supports parallel tasks)

- **Parallelize only independent chunks.** Safe fan-outs: the simulator zoo in
  Phase 2 (one family per agent); Monte Carlo coverage tests; docs drafting.
  Never parallel: anything touching `card.py`/`integrity.py` semantics,
  storage migration, threshold changes.
- **One writer per file.** Two agents never edit the same module in flight.
- **Integrator verifies.** The main thread re-runs the full suite AND
  spot-checks each subagent's claims against actual output before accepting
  (run one of their tests yourself; diff their numbers against a rerun).
  Subagent reports are hypotheses until reproduced.
- **No subagent may change an `integrity.py` threshold.** Thresholds change
  only in the main thread, only with a bench result file cited.
- Give each subagent: the file list it owns, the acceptance test it must pass,
  and the notebook section it must append to. Merge notebook sections verbatim.

---

## 9. Definition of done & handoff

The run is complete when Phase 4's gate passes (Phase 5 is a bonus). Then:

1. Final GAUGE.md session entry: phases completed, headline numbers
   (test count before/after, bench FPR/power table summary, corrected flagship
   card deltas), and explicit list of anything skipped or blocked.
2. `lab/HANDOFF.md`: (a) every LRN/MST/DEC worth porting to engram,
   (b) exact review checklist for Satish (files to read in order,
   commands to run, decisions that need his sign-off — e.g. the D2 definition
   change and the v0.3.0 release), (c) known remaining gaps, ranked.
3. Leave the working tree clean: everything committed on `northstar`,
   `master` untouched, nothing pushed, nothing published.

Honesty of the handoff outranks completeness of the work. An accurate "Phase 3
half-done, here is exactly where and why" is a success; a glossy summary that
overstates coverage is the one unforgivable failure mode for a project whose
entire premise is calibrated self-assessment.

# Caliber Record And Verification Spec

Spec version: `0.2`

Status: Round Two Phase B. This document specifies the record, event-log,
commitment, anchor, Trust Card, `verify-log`, and `verify-card` behavior that
exists in the current Caliber codebase. Version `0.2` adds optional signed
cards and external adjudication. It does not specify network anchoring,
multi-class outcomes, or Phase C succession gates.

Normative keywords `MUST`, `MUST NOT`, `SHOULD`, and `MAY` are used in their
ordinary RFC sense.

## 1. Versioning

The spec version for this document is `0.2`.

Trust Card JSON currently uses:

```json
{"trust_version": "0.1"}
```

Event-log entries currently use:

```json
{"version": 1}
```

A verifier for this spec MUST support Trust Card `trust_version` `"0.1"`,
the optional v0.2 signed-card and adjudication fields below, and event
`version` `1`.

## 2. Prediction Records

A prediction record is a JSON object with these fields:

| field | type | required | constraints |
| --- | --- | --- | --- |
| `id` | string | yes | Non-empty prediction identifier. |
| `claim` | string | yes | Prediction text. |
| `confidence` | number | yes | Inclusive range `[0.50, 0.99]`. |
| `domain` | string | yes | Domain/category label. |
| `timestamp` | string | yes | ISO 8601 datetime accepted by Python `datetime.fromisoformat`. |
| `outcome` | boolean or null | yes | `true` = correct, `false` = incorrect, `null` = unverified. |
| `verified_at` | string or null | yes | ISO 8601 datetime or `null`. |
| `notes` | string or null | yes | Optional outcome note. |
| `commitment_hash` | string | no | Lowercase SHA-256 hex digest when present. |
| `commitment_salt` | string | no | Commitment salt when present. |
| `adjudicated_by` | string | no | External adjudicator identity string. |
| `adjudicated_at` | string or null | no | ISO 8601 adjudication datetime. |
| `adjudication_note` | string or null | no | Free-text evidence note. |
| `adjudicator_signature` | string | no | Optional adjudicator signature string. |

Writers MUST reject confidence values outside `[0.50, 0.99]`. Readers SHOULD
reject records missing required fields.

## 3. Event Log

An event log is a UTF-8 JSON Lines file named:

```text
<url-quoted-agent-name>.events.jsonl
```

The URL quoting rule is `quote(agent_name, safe="")`. For example,
`agent alpha/v2` maps to `agent%20alpha%2Fv2.events.jsonl`.

Each non-empty line is one JSON object. The supported event types are:

- `predicted`
- `verified`
- `imported`
- `adjudicated`
- `anchor`

Every event object MUST have:

| field | type | rule |
| --- | --- | --- |
| `version` | integer | MUST be `1`. |
| `type` | string | MUST be one supported event type. |
| `event_id` | string | MUST be non-empty. |
| `agent_name` | string | MUST match the selected agent. |
| `created_at` | string | ISO 8601 datetime. |
| `prev_hash` | string | Previous line hash, or genesis hash for the first line. |
| `payload` | object | Type-specific payload. |

### 3.1 Canonical Serialization For Writers

Writers MUST serialize appended events as UTF-8 JSON with:

- keys sorted lexicographically;
- separators `,` and `:` with no extra whitespace;
- datetimes serialized with `datetime.isoformat()`;
- one trailing newline after each JSON object.

In Python terms, the canonical event bytes are:

```python
json.dumps(event, sort_keys=True, separators=(",", ":")).encode("utf-8")
```

### 3.2 Hash-Chain Rule

The genesis hash is 64 zero characters:

```text
0000000000000000000000000000000000000000000000000000000000000000
```

For verification, the verifier MUST split the file into lines, excluding line
terminators. For each line:

1. The line MUST be non-empty.
2. The line MUST decode as UTF-8 and parse as JSON.
3. `event.prev_hash` MUST equal the previous hash.
4. The event MUST satisfy every rule in the event-object table of section 2:
   `version` is the integer `1` (booleans are rejected), `type` is a supported
   event type, `event_id` is a non-empty string, `agent_name` equals the
   selected agent, `created_at` is an ISO 8601 datetime string, `prev_hash` is
   a string, and `payload` is a JSON object. Verification MUST fail at the
   first violating line.
5. The new previous hash becomes `SHA256(raw_line_bytes).hexdigest()`.

Payload-internal rules (section 3.3) are enforced during store reconstruction
(section 4), not by log verification.

The verifier MUST hash the raw line bytes it accepted. It MUST NOT reserialize
the JSON before hashing. This matches current `verify-log` behavior and is
what lets byte edits change the head hash.

The log head is the last computed hash. An empty missing log has structural
head equal to the genesis hash at the library level, but the `caliber
verify-log` CLI MUST fail when no event-log file exists for the selected agent.

If an expected head is provided, verification MUST also fail when the computed
head does not equal that expected head.

### 3.3 Event Payloads

`predicted` payload:

```json
{"prediction": {"...": "prediction record with outcome usually null"}}
```

`imported` payload:

```json
{"prediction": {"...": "prediction record, often already verified"}}
```

`verified` payload:

```json
{
  "prediction_id": "p1",
  "outcome": true,
  "verified_at": "2026-07-04T12:05:00+00:00",
  "notes": "optional note"
}
```

For `verified`, `outcome` MUST be boolean. `verified_at` MAY be `null`, though
writers SHOULD provide an ISO 8601 datetime. `notes` MAY be `null`.

`adjudicated` payload:

```json
{
  "prediction_id": "p1",
  "outcome": false,
  "adjudicated_at": "2026-07-05T12:30:00+00:00",
  "adjudicator": "external-reviewer@example.com",
  "evidence_note": "public evidence note",
  "adjudicator_signature": "optional signature"
}
```

For `adjudicated`, `outcome` MUST be boolean, `adjudicator` MUST be a
non-empty identity string, `adjudicated_at` SHOULD be an ISO 8601 datetime,
`evidence_note` MAY be `null`, and `adjudicator_signature` MAY be `null`.

`anchor` payload:

```json
{
  "anchored_head": "<previous-log-head>",
  "anchored_event_count": 2,
  "label": "optional label"
}
```

Anchor events do not change reconstructed predictions.

## 4. Reconstructing A Store From Events

A verifier rebuilding a prediction store MUST process events in log order:

1. `predicted` and `imported`: parse `payload.prediction` as a prediction
   record and store it by `prediction.id`, replacing any prior record with the
   same ID.
2. `verified`: find `payload.prediction_id`; if absent, fail verification.
   Set that prediction's `outcome`, `verified_at`, and `notes` fields from the
   payload.
3. `adjudicated`: find `payload.prediction_id`; if absent, fail verification.
   Set that prediction's `outcome`, `verified_at`, `notes`,
   `adjudicated_by`, `adjudicated_at`, `adjudication_note`, and
   `adjudicator_signature` fields from the payload. This marks the outcome as
   externally adjudicated rather than self-verified.
4. `anchor`: ignore for prediction reconstruction.
5. Unknown event type: fail verification.

The JSON snapshot file `<url-quoted-agent-name>.json` is a derived cache. When
an event log exists, verifiers MUST prefer the event log over the snapshot.

## 5. Commitment

Commitments bind prediction fields to a salted SHA-256 hash. The canonical
commitment string is:

```text
{claim}|{confidence:.4f}|{domain}|{timestamp.isoformat()}|{salt}
```

The commitment hash is:

```text
SHA256(canonical_commitment_string.encode()).hexdigest()
```

Current writers generate `salt` with `secrets.token_hex(16)`.

An unanchored commitment proves only that the revealed fields match the stored
hash. It does not prove when the hash existed if the hash, salt, prediction,
and verification all live in the same mutable local store.

An anchored event-log head can support third-party tamper evidence from that
head forward if the head was saved outside the mutable local store. A local
anchor event without an externally saved head is still self-attestation.

## 6. Anchor Semantics

`caliber anchor` verifies the current log, appends an `anchor` event whose
payload contains the current head and event count, and prints both:

- `anchored_head`: the head before appending the anchor event;
- `new_head`: the head after appending the anchor event.

To verify the full anchored log later, use `new_head` as the expected head:

```bash
caliber --agent <agent> --store <store> verify-log --head <new-head>
```

If only `anchored_head` is saved externally, it proves the pre-anchor prefix
but not the anchor event itself.

With `--emit <file>`, `caliber anchor` also appends one JSON line to a separate
anchors file. The emitted object has:

| field | type | rule |
| --- | --- | --- |
| `version` | integer | Current value `1`. |
| `agent_name` | string | Selected agent. |
| `created_at` | string | ISO 8601 emit time. |
| `anchored_head` | string | Head before the internal anchor event. |
| `new_head` | string | Head after the internal anchor event. |
| `event_count_before` | integer | Event count before anchoring. |
| `event_count_after` | integer | Event count after anchoring. |
| `label` | string or null | Optional label. |

The emitted file is append-only from Caliber's perspective and is intended to
be committed to git or published elsewhere as an external witness. It is not a
network operation.

## 7. Trust Card JSON

A Trust Card is a JSON object:

| field | type | rule |
| --- | --- | --- |
| `trust_version` | string | Current value `"0.1"`. |
| `agent_name` | string | Agent name. |
| `generated` | string | ISO 8601 generation datetime. |
| `calibration` | object | Calibration statistics below. |
| `integrity` | object | Optional when generated with integrity attachment. |
| `signature` | object | Optional v0.2 Ed25519 signature envelope. |

### 7.1 Calibration Object

Required calibration fields:

| field | type | formula |
| --- | --- | --- |
| `total_predictions` | integer | Number of predictions supplied to card generation. |
| `total_verified` | integer | Number with non-null `outcome`. |

When at least one prediction is verified and the card contains no externally
adjudicated outcomes, these fields MUST be present:

| field | rounding | formula |
| --- | ---: | --- |
| `overall_accuracy` | 3 decimals | `correct / total_verified` |
| `mean_confidence` | 3 decimals | `sum(confidence_i) / total_verified` |
| `mean_calibration_gap` | 3 decimals | Weighted mean of non-empty fixed-bucket gaps. |
| `brier_score` | 4 decimals | `mean((confidence_i - outcome_i)^2)` |
| `reliability` | 4 decimals | Murphy reliability term grouped by exact confidence value. |
| `resolution` | 4 decimals | Murphy resolution term grouped by exact confidence value. |
| `uncertainty` | 4 decimals | `base_rate * (1 - base_rate)` |
| `calibration_z` | 4 decimals | Spiegelhalter Z. |
| `calibration_p` | 4 decimals | Two-sided normal p-value for `calibration_z`. |

When a card contains any externally adjudicated predictions, `overall_accuracy`
MUST be omitted to avoid blending self-verified and adjudicated outcomes into
one number. The other calibration fields in the table above are computed on the
self-verified subset when that subset is non-empty. The card MUST include:

| field | type | rule |
| --- | --- | --- |
| `accuracy_basis` | string | Current value `"self_verified"`; legacy calibration views are computed on self-verified predictions only. |
| `self_verified` | object | Accuracy section for non-adjudicated verified predictions. |
| `adjudicated` | object | Accuracy section for externally adjudicated predictions. |

Each accuracy section contains `predictions` and `correct`. Non-empty sections
also contain `accuracy = correct / predictions` and `ci95`, the Wilson interval
for that section's accuracy. These two sections MUST NOT be combined into an
aggregate accuracy field.

Outcomes are encoded as `1` for `true` and `0` for `false`.

Murphy decomposition:

```text
Brier = reliability - resolution + uncertainty
```

Spiegelhalter Z:

```text
Z = sum(outcome_i - confidence_i) / sqrt(sum(confidence_i * (1 - confidence_i)))
```

If the denominator is zero, `calibration_z` and `calibration_p` MUST be
omitted.

### 7.2 Fixed Confidence Buckets

`confidence_buckets` MUST contain these labels in this order:

```text
50-59, 60-69, 70-79, 80-89, 90-99
```

Bucket inclusion is inclusive at both ends:

| label | confidence range |
| --- | --- |
| `50-59` | `0.50 <= confidence <= 0.59` |
| `60-69` | `0.60 <= confidence <= 0.69` |
| `70-79` | `0.70 <= confidence <= 0.79` |
| `80-89` | `0.80 <= confidence <= 0.89` |
| `90-99` | `0.90 <= confidence <= 0.99` |

Each bucket always has:

| field | type |
| --- | --- |
| `predictions` | integer |
| `correct` | integer |

For non-empty buckets, add:

| field | rounding | formula |
| --- | ---: | --- |
| `mean_confidence` | 3 decimals | Mean confidence inside bucket. |
| `accuracy` | 3 decimals | `correct / predictions` |
| `ci95` | 3 decimals per bound | Wilson interval for bucket accuracy. |
| `calibration_gap` | 3 decimals | `mean_confidence - accuracy` |
| `significant` | boolean | Present only when exact binomial test runs. |
| `insufficient_data` | boolean | Present and `true` when `predictions < 5`. |

Wilson interval:

```text
z = 1.959963984540054
p_hat = correct / predictions
center = (p_hat + z^2 / (2n)) / (1 + z^2 / n)
half = z * sqrt(p_hat(1 - p_hat) / n + z^2 / (4n^2)) / (1 + z^2 / n)
ci95 = [max(0, center - half), min(1, center + half)]
```

The exact binomial test runs only when `predictions >= 5`. It uses null
probability `p0 = mean_confidence` and sums all binomial outcomes whose PMF is
less than or equal to the observed PMF times `(1 + 1e-9)`. `significant` is
`true` when the two-sided p-value is `< 0.05`.

`danger_zones` MAY be present. A label enters `danger_zones` only when
`calibration_gap > 0.10` and `significant is true`.

`strength_zones` MAY be present. A label enters `strength_zones` only when
`calibration_gap < -0.10` and `significant is true`.

### 7.3 Adaptive Buckets

`adaptive_buckets` is present when there are verified predictions. To build it:

1. Sort verified predictions by confidence ascending.
2. Let `bucket_count = min(n, max(3, ceil(n / 25)))`.
3. For index `i` from `0` to `bucket_count - 1`, select
   `ordered[i*n//bucket_count : (i+1)*n//bucket_count]`.

Each adaptive bucket has:

| field | rounding | rule |
| --- | ---: | --- |
| `index` | none | 1-based bucket index. |
| `predictions` | none | Bucket size. |
| `correct` | none | Correct count. |
| `confidence_range` | 3 decimals per value | `[min_confidence, max_confidence]`. |
| `mean_confidence` | 3 decimals | Mean confidence. |
| `accuracy` | 3 decimals | `correct / predictions`. |
| `ci95` | 3 decimals per bound | Wilson interval. |
| `calibration_gap` | 3 decimals | `mean_confidence - accuracy`. |

### 7.4 Domain Statistics

`domains` maps domain name to:

| field | rounding | formula |
| --- | ---: | --- |
| `predictions` | none | Verified predictions in that domain. |
| `correct` | none | Correct count. |
| `avg_confidence` | 3 decimals | Mean confidence in domain. |
| `accuracy` | 3 decimals | `correct / predictions`. |

Domains are serialized in sorted domain-name order.

### 7.5 Optional Integrity Attachment

When a card includes `integrity`, `verify-card` MUST recompute integrity from
the same event-log-backed prediction store and compare it. The current
integrity object contains:

- `agent_name`
- `generated`
- `n_verified`
- `verdict`
- optional `metrics`
- `flags`

The exact metric and flag semantics are implementation-defined, but verifiers
MUST compare the saved object to the recomputed object after stripping all
`generated` fields.

Spec version `0.2` includes `adjudicated_share` in the optional integrity
metrics object when verified predictions exist. It is the share of verified
predictions with an adjudicator identity. It is a reported metric only, not a
flag.

### 7.6 Optional Signature Envelope

Signed cards have a top-level `signature` object:

```json
{
  "algorithm": "Ed25519",
  "event_log_head": "<64 lowercase hex characters>",
  "signature": "<base64 Ed25519 signature>"
}
```

The signing extra is optional: writers that implement signing use
`caliber-trust[signing]`, which depends on `cryptography`. Core readers and
writers MUST NOT require this dependency unless signing or signature
verification is requested.

The signed bytes are:

```text
"caliber-card-signature-v1\n"
+ event_log_head
+ "\n"
+ canonical_card_json_without_signature
```

`canonical_card_json_without_signature` is the Trust Card JSON object with the
top-level `signature` field removed, serialized with sorted keys and compact
separators:

```python
json.dumps(card_without_signature, sort_keys=True, separators=(",", ":")).encode("utf-8")
```

Signature verification with `--pubkey` MUST verify the Ed25519 signature and
MUST fail if `signature.event_log_head` does not equal the current verified
event-log head. Ordinary `verify-card` without `--pubkey` MUST strip the
top-level signature envelope before comparing card statistics.

## 8. `verify-log` Algorithm

Inputs:

- selected `agent_name`;
- selected store directory;
- optional expected head hash.

Algorithm:

1. Compute the event-log path from the selected agent name.
2. If the file does not exist, fail.
3. Set `previous_hash` to the genesis hash.
4. For each raw line in order, starting at line `1`:
   - fail on an empty line;
   - decode UTF-8 and parse JSON, failing on errors;
   - fail if `event.prev_hash != previous_hash`;
   - set `previous_hash = SHA256(raw_line_bytes).hexdigest()`.
5. If an expected head was supplied and differs from `previous_hash`, fail.
6. Otherwise pass with `event_count` and `head_hash`.

Expected JSON output shape:

```json
{
  "agent_name": "vector-agent",
  "path": "/path/to/vector-agent.events.jsonl",
  "valid": true,
  "event_count": 3,
  "head_hash": "<computed-head>",
  "error": null,
  "failed_line": null
}
```

## 9. `verify-card` Algorithm

Inputs:

- selected `agent_name`;
- selected store directory;
- saved card JSON path.
- optional Ed25519 public key path.

Algorithm:

1. Load the saved card JSON.
2. Fail if `saved_card.agent_name` does not equal the selected `agent_name`.
3. Verify that the selected agent's event log exists.
4. Run the `verify-log` algorithm. Fail if the event log is invalid.
5. Reconstruct predictions from the event log.
6. Generate a Trust Card from reconstructed verified predictions.
7. If the saved card has an `integrity` field, recompute integrity and attach
   it to the recomputed card.
8. If a public key was supplied, verify the saved card's signature envelope
   using section 7.6. Fail if the signature is absent, malformed, invalid, or
   bound to any head other than the current verified event-log head.
9. Remove the top-level `signature` field from the saved card before ordinary
   card-stat comparison.
10. Recursively remove every `generated` field from both saved and recomputed
   JSON objects.
11. Compare objects exactly:
   - dictionary key sets MUST match;
   - list lengths and order MUST match;
   - primitive values MUST match.
12. Fail on the first mismatch; otherwise pass.

Expected JSON output shape:

```json
{
  "card_path": "/path/to/card.json",
  "agent_name": "vector-agent",
  "valid": true,
  "checked": ["calibration"],
  "event_log_head": "<computed-head>",
  "event_count": 5,
  "error": null
}
```

## 10. Golden Test Vectors

Executable vectors live under `tests/vectors/`:

| file | purpose |
| --- | --- |
| `manifest.json` | Expected heads, event counts, and tamper failure. |
| `log-valid/vector-agent.events.jsonl` | Valid log with `predicted`, `verified`, and `anchor` events. |
| `log-tampered/vector-agent.events.jsonl` | First event claim edited without updating later `prev_hash`. |
| `log-structural/vector-agent.events.jsonl` | Chain-valid log whose second event has an unsupported `type`. |
| `card.json` | Saved Trust Card. |
| `card-store/vector-agent.events.jsonl` | Event-log-backed store that produces `card.json`. |
| `card-store/vector-agent.json` | Derived JSON snapshot cache for the same store. |
| `adjudicated-card.json` | Saved Trust Card with split self-verified/adjudicated accuracy. |
| `adjudicated-store/vector-agent.events.jsonl` | Event-log-backed store containing an `adjudicated` event. |
| `adjudicated-store/vector-agent.json` | Derived JSON snapshot cache for the adjudicated store. |

The vector-validating test is:

```bash
python -m pytest tests/test_spec_vectors.py -q
```

Vector expectations:

```json
{
  "valid_log_head": "ab5f201068385c1644d4ba62b37977ea7201009100c902e70610641de67ac442",
  "tampered_failure": "prev_hash does not match previous line hash",
  "tampered_failed_line": 2,
  "structural_failure": "unsupported event type: 'banana'",
  "structural_failed_line": 2,
  "card_store_head": "9f23e8157f376de86ce3c01115b6900188a60e2b932592ef340b0cf873e8e72a",
  "adjudicated_store_head": "d16b1d7b9ae039c705da8ab40b163988334e74f47dea0eb9fce95bf4653c5517"
}
```

These vectors are part of the spec. A second implementation of `verify-log`
and `verify-card` should pass them without importing Caliber code.

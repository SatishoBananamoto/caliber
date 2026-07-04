# Caliber Record And Verification Spec

Spec version: `0.1`

Status: Round Two Phase A. This document specifies the record, event-log,
commitment, anchor, Trust Card, `verify-log`, and `verify-card` behavior that
exists in the current Caliber codebase. It does not specify signed cards,
external adjudication, network anchoring, multi-class outcomes, or any Phase B
feature.

Normative keywords `MUST`, `MUST NOT`, `SHOULD`, and `MAY` are used in their
ordinary RFC sense.

## 1. Versioning

The spec version for this document is `0.1`.

Trust Card JSON currently uses:

```json
{"trust_version": "0.1"}
```

Event-log entries currently use:

```json
{"version": 1}
```

A verifier for this spec MUST support Trust Card `trust_version` `"0.1"` and
event `version` `1`.

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
4. The new previous hash becomes `SHA256(raw_line_bytes).hexdigest()`.

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
3. `anchor`: ignore for prediction reconstruction.
4. Unknown event type: fail verification.

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

## 7. Trust Card JSON

A Trust Card is a JSON object:

| field | type | rule |
| --- | --- | --- |
| `trust_version` | string | Current value `"0.1"`. |
| `agent_name` | string | Agent name. |
| `generated` | string | ISO 8601 generation datetime. |
| `calibration` | object | Calibration statistics below. |
| `integrity` | object | Optional when generated with integrity attachment. |

### 7.1 Calibration Object

Required calibration fields:

| field | type | formula |
| --- | --- | --- |
| `total_predictions` | integer | Number of predictions supplied to card generation. |
| `total_verified` | integer | Number with non-null `outcome`. |

When at least one prediction is verified, these fields MUST be present:

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

The exact metric and flag semantics are implementation-defined for spec
version `0.1`, but verifiers MUST compare the saved object to the recomputed
object after stripping all `generated` fields.

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

Algorithm:

1. Load the saved card JSON.
2. Fail if `saved_card.agent_name` does not equal the selected `agent_name`.
3. Verify that the selected agent's event log exists.
4. Run the `verify-log` algorithm. Fail if the event log is invalid.
5. Reconstruct predictions from the event log.
6. Generate a Trust Card from reconstructed verified predictions.
7. If the saved card has an `integrity` field, recompute integrity and attach
   it to the recomputed card.
8. Recursively remove every `generated` field from both saved and recomputed
   JSON objects.
9. Compare objects exactly:
   - dictionary key sets MUST match;
   - list lengths and order MUST match;
   - primitive values MUST match.
10. Fail on the first mismatch; otherwise pass.

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
| `card.json` | Saved Trust Card. |
| `card-store/vector-agent.events.jsonl` | Event-log-backed store that produces `card.json`. |
| `card-store/vector-agent.json` | Derived JSON snapshot cache for the same store. |

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
  "card_store_head": "9f23e8157f376de86ce3c01115b6900188a60e2b932592ef340b0cf873e8e72a"
}
```

These vectors are part of the spec. A second implementation of `verify-log`
and `verify-card` should pass them without importing Caliber code.

"""Deterministic prediction-stream simulators for the adversarial lab.

The lab is not shipped with the package. Simulators return dictionaries that
can be passed to ``Prediction(**record)`` so benchmark code can stay decoupled
from storage and CLI concerns.
"""

from __future__ import annotations

import math
import random
from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from typing import Any

from caliber.tracker import Prediction


T0 = datetime(2026, 7, 4, 12, 0, 0, tzinfo=timezone.utc)
DOMAINS = ("codebase", "behavior", "architecture", "tooling", "facts")
CLAIM_ADJECTIVES = (
    "cached",
    "parsed",
    "remote",
    "local",
    "signed",
    "queued",
    "validated",
    "indexed",
    "rendered",
    "compiled",
)
CLAIM_SUBJECTS = (
    "module",
    "route",
    "schema",
    "adapter",
    "worker",
    "command",
    "fixture",
    "policy",
    "report",
    "cache",
)
CLAIM_VERBS = (
    "accepts",
    "rejects",
    "loads",
    "persists",
    "normalizes",
    "sorts",
    "streams",
    "validates",
    "summarizes",
    "anchors",
)
CLAIM_OBJECTS = (
    "payloads",
    "settings",
    "events",
    "snapshots",
    "tokens",
    "records",
    "messages",
    "artifacts",
    "headers",
    "results",
)

Record = dict[str, Any]
Simulator = Callable[[int, int], list[Record]]


def _clip_confidence(value: float) -> float:
    return min(0.99, max(0.50, round(value, 3)))


def _bernoulli(rng: random.Random, p: float) -> bool:
    return rng.random() < p


def _lognormal_latency_seconds(rng: random.Random) -> float:
    # Median ~= 10 minutes; sigma keeps a broad but practical tail.
    return max(1.0, rng.lognormvariate(math.log(600.0), 0.8))


def _record(
    i: int,
    *,
    claim: str,
    confidence: float,
    domain: str,
    outcome: bool,
    latency_seconds: float,
    imported: bool = False,
    prefix: str = "sim",
) -> Record:
    timestamp = T0 + timedelta(minutes=i)
    verified_at = timestamp if imported else timestamp + timedelta(seconds=latency_seconds)
    return {
        "id": f"{prefix}-{i:05d}",
        "claim": claim,
        "confidence": _clip_confidence(confidence),
        "domain": domain,
        "timestamp": timestamp,
        "outcome": outcome,
        "verified_at": verified_at,
        "notes": None,
    }


def _latent_probability(rng: random.Random, sharpness: float) -> float:
    """Draw an honest event probability in [0.50, 0.99].

    Beta(sharpness, sharpness) is symmetric on [0, 1]; mapping it to
    [0.50, 0.99] gives a mean near 0.745. Lower sharpness gives more extreme
    probabilities, while higher sharpness clusters around the middle.
    """
    sharpness = max(0.05, sharpness)
    return 0.50 + 0.49 * rng.betavariate(sharpness, sharpness)


def _letter_token(i: int) -> str:
    letters = []
    value = i
    while True:
        value, rem = divmod(value, 26)
        letters.append(chr(ord("a") + rem))
        if value == 0:
            break
    return "".join(reversed(letters))


def _honest_claim(i: int, domain: str) -> str:
    return (
        f"{CLAIM_ADJECTIVES[i % len(CLAIM_ADJECTIVES)]} {domain} "
        f"{CLAIM_SUBJECTS[(i * 3) % len(CLAIM_SUBJECTS)]} "
        f"{CLAIM_VERBS[(i * 5 + 1) % len(CLAIM_VERBS)]} "
        f"{CLAIM_OBJECTS[(i * 7 + 2) % len(CLAIM_OBJECTS)]} "
        f"marker{_letter_token(i)} path{_letter_token(i * 7 + 3)}"
    )


def _honest_record(
    rng: random.Random,
    i: int,
    *,
    sharpness: float = 2.0,
    confidence_delta: float = 0.0,
    noise_sigma: float = 0.0,
    prefix: str = "honest",
) -> Record:
    p = _latent_probability(rng, sharpness)
    confidence = p + confidence_delta
    if noise_sigma:
        confidence += rng.gauss(0.0, noise_sigma)
    domain = DOMAINS[i % len(DOMAINS)]
    return _record(
        i,
        claim=_honest_claim(i, domain),
        confidence=confidence,
        domain=domain,
        outcome=_bernoulli(rng, p),
        latency_seconds=_lognormal_latency_seconds(rng),
        prefix=prefix,
    )


def _reindex(records: list[Record], prefix: str) -> list[Record]:
    reindexed = []
    for i, record in enumerate(records):
        item = dict(record)
        item["id"] = f"{prefix}-{i:05d}"
        item["timestamp"] = T0 + timedelta(minutes=i)
        if item["verified_at"] == record["timestamp"]:
            item["verified_at"] = item["timestamp"]
        else:
            delta = record["verified_at"] - record["timestamp"]
            item["verified_at"] = item["timestamp"] + delta
        reindexed.append(item)
    return reindexed


def to_predictions(records: list[Record]) -> list[Prediction]:
    return [Prediction(**record) for record in records]


def honest(n: int, seed: int, *, sharpness: float = 2.0) -> list[Record]:
    rng = random.Random(seed)
    return [
        _honest_record(rng, i, sharpness=sharpness, prefix="honest")
        for i in range(n)
    ]


def overconfident(
    n: int,
    seed: int,
    *,
    delta: float = 0.15,
    sharpness: float = 2.0,
) -> list[Record]:
    rng = random.Random(seed)
    return [
        _honest_record(
            rng,
            i,
            sharpness=sharpness,
            confidence_delta=abs(delta),
            prefix="over",
        )
        for i in range(n)
    ]


def underconfident(
    n: int,
    seed: int,
    *,
    delta: float = 0.15,
    sharpness: float = 2.0,
) -> list[Record]:
    rng = random.Random(seed)
    return [
        _honest_record(
            rng,
            i,
            sharpness=sharpness,
            confidence_delta=-abs(delta),
            prefix="under",
        )
        for i in range(n)
    ]


def noisy(
    n: int,
    seed: int,
    *,
    sigma: float = 0.15,
    sharpness: float = 2.0,
) -> list[Record]:
    rng = random.Random(seed)
    return [
        _honest_record(
            rng,
            i,
            sharpness=sharpness,
            noise_sigma=sigma,
            prefix="noisy",
        )
        for i in range(n)
    ]


def farmer(n: int, seed: int, *, easy_share: float = 0.85) -> list[Record]:
    rng = random.Random(seed)
    easy_n = round(n * easy_share)
    records: list[Record] = []
    for i in range(easy_n):
        records.append(
            _record(
                i,
                claim=f"file number {i} exists on disk",
                confidence=0.95 + 0.03 * rng.random(),
                domain="filesystem",
                outcome=_bernoulli(rng, 0.98),
                latency_seconds=5.0 + rng.random() * 20.0,
                prefix="farmer",
            )
        )
    for i in range(easy_n, n):
        records.append(_honest_record(rng, i, prefix="farmer"))
    return records


def patient_farmer(n: int, seed: int, *, easy_share: float = 0.85) -> list[Record]:
    records = farmer(n, seed, easy_share=easy_share)
    easy_n = round(n * easy_share)
    for i, record in enumerate(records[:easy_n]):
        timestamp = record["timestamp"]
        record["verified_at"] = timestamp + timedelta(minutes=3, seconds=i % 17)
    return records


def naive_fabricator(n: int, seed: int) -> list[Record]:
    rng = random.Random(seed)
    confidences = [0.60, 0.70, 0.80, 0.90]
    records: list[Record] = []
    for bucket_index, confidence in enumerate(confidences):
        start = bucket_index * n // len(confidences)
        end = (bucket_index + 1) * n // len(confidences)
        size = end - start
        correct_n = round(confidence * size)
        outcomes = [True] * correct_n + [False] * (size - correct_n)
        rng.shuffle(outcomes)
        for offset, outcome in enumerate(outcomes):
            i = start + offset
            domain = DOMAINS[i % 3]
            records.append(
                _record(
                    i,
                    claim=f"fabricated but distinct claim {i}",
                    confidence=confidence,
                    domain=domain,
                    outcome=outcome,
                    latency_seconds=_lognormal_latency_seconds(rng),
                    prefix="naive-fabricator",
                )
            )
    return sorted(records, key=lambda record: record["timestamp"])


def smart_fabricator(n: int, seed: int) -> list[Record]:
    rng = random.Random(seed)
    records = []
    for i in range(n):
        confidence = _clip_confidence(0.50 + 0.49 * rng.random())
        domain = DOMAINS[i % len(DOMAINS)]
        records.append(
            _record(
                i,
                claim=_honest_claim(i, domain),
                confidence=confidence,
                domain=domain,
                outcome=_bernoulli(rng, confidence),
                latency_seconds=_lognormal_latency_seconds(rng),
                prefix="smart-fabricator",
            )
        )
    return records


def template_spammer(n: int, seed: int) -> list[Record]:
    rng = random.Random(seed)
    records = []
    for i in range(n):
        confidence = [0.55, 0.75, 0.92][i % 3]
        records.append(
            _record(
                i,
                claim=f"package number {i} is maintained upstream",
                confidence=confidence,
                domain=DOMAINS[i % 3],
                outcome=_bernoulli(rng, confidence),
                latency_seconds=_lognormal_latency_seconds(rng),
                prefix="template",
            )
        )
    return records


def domain_camper(n: int, seed: int, *, k_domains: int = 1) -> list[Record]:
    rng = random.Random(seed)
    k = max(1, min(k_domains, len(DOMAINS)))
    records = []
    for i in range(n):
        record = _honest_record(rng, i, prefix="domain-camper")
        record["domain"] = DOMAINS[i % k]
        record["claim"] = f"{record['domain']} narrow-domain claim {i}"
        records.append(record)
    return records


def bulk_importer(n: int, seed: int, *, import_share: float = 0.85) -> list[Record]:
    rng = random.Random(seed)
    imported_n = round(n * import_share)
    records = honest(n, seed, sharpness=1.5)
    for i, record in enumerate(records):
        record["id"] = f"bulk-{i:05d}"
        record["claim"] = f"backfilled calibration claim {i}"
        if i < imported_n:
            record["verified_at"] = record["timestamp"]
        else:
            record["verified_at"] = record["timestamp"] + timedelta(
                seconds=_lognormal_latency_seconds(rng)
            )
    return records


def mixture(
    n: int,
    seed: int,
    *,
    honest_frac: float = 0.5,
    attacker: Callable[..., list[Record]] = farmer,
    **attacker_kwargs: Any,
) -> list[Record]:
    honest_n = round(n * honest_frac)
    attack_n = n - honest_n
    records = honest(honest_n, seed, sharpness=2.0)
    records.extend(attacker(attack_n, seed + 1, **attacker_kwargs))
    return _reindex(records, "mixture")


POPULATIONS: dict[str, Simulator] = {
    "honest": honest,
    "overconfident": overconfident,
    "underconfident": underconfident,
    "noisy": noisy,
    "farmer": farmer,
    "patient_farmer": patient_farmer,
    "naive_fabricator": naive_fabricator,
    "smart_fabricator": smart_fabricator,
    "template_spammer": template_spammer,
    "domain_camper": domain_camper,
    "bulk_importer": bulk_importer,
}

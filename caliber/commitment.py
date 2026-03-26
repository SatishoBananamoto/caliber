"""Prediction commitment scheme — proves predictions were made before verification.

When a prediction is committed:
1. A salt is generated
2. commitment = SHA256(claim | confidence | domain | timestamp | salt)
3. The commitment hash is stored (can be published)
4. At verification time, the full data is revealed
5. Anyone can verify: SHA256(revealed_data) == stored_commitment

This prevents retroactive fabrication of predictions.
No blockchain. No external service. Just SHA256 + salt.
"""

from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Commitment:
    """A cryptographic commitment to a prediction."""

    commitment_hash: str
    salt: str
    committed_at: datetime

    def to_dict(self) -> dict:
        return {
            "commitment_hash": self.commitment_hash,
            "salt": self.salt,
            "committed_at": self.committed_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> Commitment:
        return cls(
            commitment_hash=data["commitment_hash"],
            salt=data["salt"],
            committed_at=datetime.fromisoformat(data["committed_at"]),
        )


def create_commitment(
    claim: str,
    confidence: float,
    domain: str,
    timestamp: datetime,
) -> Commitment:
    """Create a commitment hash for a prediction.

    The commitment proves the prediction existed at this point in time.
    The salt ensures the hash can't be reverse-engineered from the claim.
    """
    salt = secrets.token_hex(16)
    data = _commitment_data(claim, confidence, domain, timestamp, salt)
    commitment_hash = hashlib.sha256(data.encode()).hexdigest()

    return Commitment(
        commitment_hash=commitment_hash,
        salt=salt,
        committed_at=timestamp,
    )


def verify_commitment(
    commitment: Commitment,
    claim: str,
    confidence: float,
    domain: str,
    timestamp: datetime,
) -> bool:
    """Verify that a commitment matches the revealed prediction data.

    Returns True if the prediction data matches the commitment hash.
    """
    data = _commitment_data(claim, confidence, domain, timestamp, commitment.salt)
    expected_hash = hashlib.sha256(data.encode()).hexdigest()
    return expected_hash == commitment.commitment_hash


def _commitment_data(
    claim: str,
    confidence: float,
    domain: str,
    timestamp: datetime,
    salt: str,
) -> str:
    """Build the canonical string for hashing."""
    return f"{claim}|{confidence:.4f}|{domain}|{timestamp.isoformat()}|{salt}"

"""Tests for caliber.commitment."""

from datetime import datetime, timezone

from caliber.commitment import create_commitment, verify_commitment
from caliber.tracker import TrustTracker
from caliber.storage import MemoryStorage


class TestCommitment:
    def test_create(self):
        ts = datetime(2026, 3, 26, tzinfo=timezone.utc)
        c = create_commitment("sky is blue", 0.90, "facts", ts)
        assert len(c.commitment_hash) == 64  # SHA-256 hex
        assert len(c.salt) == 32  # 16 bytes hex

    def test_verify_correct(self):
        ts = datetime(2026, 3, 26, tzinfo=timezone.utc)
        c = create_commitment("sky is blue", 0.90, "facts", ts)
        assert verify_commitment(c, "sky is blue", 0.90, "facts", ts)

    def test_verify_wrong_claim(self):
        ts = datetime(2026, 3, 26, tzinfo=timezone.utc)
        c = create_commitment("sky is blue", 0.90, "facts", ts)
        assert not verify_commitment(c, "sky is green", 0.90, "facts", ts)

    def test_verify_wrong_confidence(self):
        ts = datetime(2026, 3, 26, tzinfo=timezone.utc)
        c = create_commitment("sky is blue", 0.90, "facts", ts)
        assert not verify_commitment(c, "sky is blue", 0.80, "facts", ts)

    def test_different_salts(self):
        ts = datetime(2026, 3, 26, tzinfo=timezone.utc)
        c1 = create_commitment("sky is blue", 0.90, "facts", ts)
        c2 = create_commitment("sky is blue", 0.90, "facts", ts)
        # Same data but different salts → different hashes
        assert c1.commitment_hash != c2.commitment_hash

    def test_roundtrip(self):
        ts = datetime(2026, 3, 26, tzinfo=timezone.utc)
        c = create_commitment("test", 0.75, "x", ts)
        d = c.to_dict()
        c2 = type(c).from_dict(d)
        assert c2.commitment_hash == c.commitment_hash
        assert verify_commitment(c2, "test", 0.75, "x", ts)


class TestSignedTracker:
    def test_signed_predictions_have_commitment(self):
        tracker = TrustTracker("test", storage=MemoryStorage(), signed=True)
        pid = tracker.predict("test claim", 0.80, "x")
        pred = tracker.get(pid)
        assert pred.commitment_hash is not None
        assert pred.commitment_salt is not None

    def test_unsigned_predictions_no_commitment(self):
        tracker = TrustTracker("test", storage=MemoryStorage(), signed=False)
        pid = tracker.predict("test claim", 0.80, "x")
        pred = tracker.get(pid)
        assert pred.commitment_hash is None

    def test_commitment_verifies(self):
        from caliber.commitment import verify_commitment, Commitment

        tracker = TrustTracker("test", storage=MemoryStorage(), signed=True)
        pid = tracker.predict("test claim", 0.80, "x")
        pred = tracker.get(pid)

        c = Commitment(
            commitment_hash=pred.commitment_hash,
            salt=pred.commitment_salt,
            committed_at=pred.timestamp,
        )
        assert verify_commitment(c, pred.claim, pred.confidence, pred.domain, pred.timestamp)

    def test_commitment_in_storage(self):
        storage = MemoryStorage()
        t1 = TrustTracker("test", storage=storage, signed=True)
        pid = t1.predict("test", 0.80, "x")

        # Load from storage
        t2 = TrustTracker("test", storage=storage)
        pred = t2.get(pid)
        assert pred.commitment_hash is not None

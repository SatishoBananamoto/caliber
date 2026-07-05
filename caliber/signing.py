"""Optional Ed25519 signing for Trust Cards.

The package core intentionally does not import ``cryptography``. This module
loads it only inside signing operations, so installations without the
``signing`` extra can still import and use caliber normally.
"""

from __future__ import annotations

import base64
import binascii
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import quote


SIGNATURE_FIELD = "signature"
SIGNATURE_ALGORITHM = "Ed25519"
SIGNATURE_PAYLOAD_PREFIX = b"caliber-card-signature-v1\n"


class SigningUnavailable(RuntimeError):
    """Raised when the optional signing dependency is not installed."""


class SignatureVerificationError(ValueError):
    """Raised when a signed card cannot be verified."""


@dataclass(frozen=True)
class KeyPaths:
    """Default signing key paths for one agent in one store."""

    private_key: Path
    public_key: Path


def default_key_paths(store: str | Path, agent_name: str) -> KeyPaths:
    """Return the default Ed25519 keypair paths for an agent."""
    safe_name = quote(agent_name, safe="")
    base = Path(store).expanduser() / f"{safe_name}.ed25519"
    return KeyPaths(
        private_key=base.with_suffix(".ed25519.private.pem"),
        public_key=base.with_suffix(".ed25519.public.pem"),
    )


def strip_signature(card: dict[str, Any]) -> dict[str, Any]:
    """Return a shallow card copy without the top-level signature envelope."""
    return {key: value for key, value in card.items() if key != SIGNATURE_FIELD}


def _require_crypto():
    try:
        from cryptography.exceptions import InvalidSignature
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric.ed25519 import (
            Ed25519PrivateKey,
            Ed25519PublicKey,
        )
    except ImportError as exc:
        raise SigningUnavailable(
            "Trust Card signing requires the optional extra: "
            "pip install 'caliber-trust[signing]'"
        ) from exc
    return InvalidSignature, serialization, Ed25519PrivateKey, Ed25519PublicKey


def _canonical_card_bytes(card: dict[str, Any]) -> bytes:
    return json.dumps(
        strip_signature(card),
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def signature_payload(card: dict[str, Any], event_log_head: str) -> bytes:
    """Canonical bytes signed for a Trust Card and event-log head."""
    return (
        SIGNATURE_PAYLOAD_PREFIX
        + event_log_head.encode("ascii")
        + b"\n"
        + _canonical_card_bytes(card)
    )


def generate_keypair(
    store: str | Path,
    agent_name: str,
    *,
    force: bool = False,
) -> KeyPaths:
    """Generate an Ed25519 keypair under the store directory."""
    _InvalidSignature, serialization, Ed25519PrivateKey, _Ed25519PublicKey = (
        _require_crypto()
    )
    paths = default_key_paths(store, agent_name)
    paths.private_key.parent.mkdir(parents=True, exist_ok=True)
    if not force and (paths.private_key.exists() or paths.public_key.exists()):
        raise FileExistsError(
            f"signing key already exists for {agent_name!r}; use --force to replace it"
        )

    private_key = Ed25519PrivateKey.generate()
    private_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_bytes = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    fd = os.open(paths.private_key, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "wb") as f:
        f.write(private_bytes)
    os.chmod(paths.private_key, 0o600)
    paths.public_key.write_bytes(public_bytes)
    return paths


def sign_card(
    card: dict[str, Any],
    event_log_head: str,
    private_key_path: str | Path,
) -> dict[str, Any]:
    """Return a signed copy of ``card`` bound to ``event_log_head``."""
    _InvalidSignature, serialization, Ed25519PrivateKey, _Ed25519PublicKey = (
        _require_crypto()
    )
    private_key = serialization.load_pem_private_key(
        Path(private_key_path).read_bytes(),
        password=None,
    )
    if not isinstance(private_key, Ed25519PrivateKey):
        raise ValueError("private key is not an Ed25519 key")
    payload = signature_payload(card, event_log_head)
    signature = private_key.sign(payload)
    signed = strip_signature(card)
    signed[SIGNATURE_FIELD] = {
        "algorithm": SIGNATURE_ALGORITHM,
        "event_log_head": event_log_head,
        "signature": base64.b64encode(signature).decode("ascii"),
    }
    return signed


def verify_card_signature(
    signed_card: dict[str, Any],
    public_key_path: str | Path,
    *,
    current_event_log_head: str | None = None,
) -> None:
    """Verify a signed Trust Card.

    Raises ``SignatureVerificationError`` for malformed envelopes, head
    mismatches, or invalid signatures.
    """
    InvalidSignature, serialization, _Ed25519PrivateKey, Ed25519PublicKey = (
        _require_crypto()
    )
    envelope = signed_card.get(SIGNATURE_FIELD)
    if not isinstance(envelope, dict):
        raise SignatureVerificationError("card has no signature envelope")
    if envelope.get("algorithm") != SIGNATURE_ALGORITHM:
        raise SignatureVerificationError(
            f"unsupported signature algorithm: {envelope.get('algorithm')!r}"
        )
    event_log_head = envelope.get("event_log_head")
    if not isinstance(event_log_head, str) or len(event_log_head) != 64:
        raise SignatureVerificationError("signature event_log_head is invalid")
    if (
        current_event_log_head is not None
        and event_log_head != current_event_log_head
    ):
        raise SignatureVerificationError(
            "signature event_log_head does not match current event log head"
        )
    encoded_signature = envelope.get("signature")
    if not isinstance(encoded_signature, str):
        raise SignatureVerificationError("signature value is missing")
    try:
        signature = base64.b64decode(encoded_signature, validate=True)
    except (ValueError, binascii.Error) as exc:
        raise SignatureVerificationError("signature is not valid base64") from exc

    try:
        public_key = serialization.load_pem_public_key(
            Path(public_key_path).read_bytes()
        )
    except (OSError, ValueError) as exc:
        raise SignatureVerificationError("public key could not be loaded") from exc
    if not isinstance(public_key, Ed25519PublicKey):
        raise SignatureVerificationError("public key is not an Ed25519 key")
    try:
        public_key.verify(signature, signature_payload(signed_card, event_log_head))
    except InvalidSignature as exc:
        raise SignatureVerificationError("signature verification failed") from exc

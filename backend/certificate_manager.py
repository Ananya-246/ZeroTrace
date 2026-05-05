"""
Tamper-proof wipe certificates: Ed25519 signatures over SHA-256 of canonical JSON.

Cryptographic flow (high level):
1. Serialize certificate fields to a canonical JSON string (sorted keys, compact separators).
2. SHA-256 digest of that UTF-8 byte string (audit-friendly fixed fingerprint).
3. Ed25519 signature over the digest bytes (signing a short fixed message is valid; verifier uses the same digest).
4. Distribute certificate.json + signature.sig + certificate.pdf; keep private_key.pem secret.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import stat
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Union

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

__all__ = [
    "generate_keys",
    "sign_data",
    "generate_certificate",
    "verify_certificate",
]

__version__ = "1.0.0"

PRIVATE_KEY_NAME = "private_key.pem"
PUBLIC_KEY_NAME = "public_key.pem"

DEFAULT_TOOL_NAME = "ZeroTrace"


def _default_keys_directory() -> Path:
    """Directory holding key material; co-located with this module under ``keys/``."""
    return Path(__file__).resolve().parent / "keys"


def _canonical_json_bytes(payload: Mapping[str, Any]) -> bytes:
    """
    Deterministic JSON bytes for hashing/signing.
    Sorted keys + compact separators avoids trivial whitespace tampering.
    """
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def sign_data(message: bytes, private_key_path: Union[str, Path]) -> bytes:
    """
    Sign arbitrary bytes with the Ed25519 private key stored at ``private_key_path``.

    For this tool, ``message`` is typically the SHA-256 digest (32 bytes) of the
    canonical JSON certificate payload.
    """
    path = Path(private_key_path)
    data = path.read_bytes()
    private_key = serialization.load_pem_private_key(data, password=None)
    if not isinstance(private_key, Ed25519PrivateKey):
        raise TypeError("private_key.pem must be an Ed25519 key")
    return private_key.sign(message)


def generate_keys(keys_directory: Union[str, Path] | None = None) -> tuple[Path, Path]:
    """
    Ensure ``private_key.pem`` and ``public_key.pem`` exist under ``keys_directory``.

    On first run, generates an Ed25519 key pair and writes PEM files.
    Sets restrictive permissions on the private key where the OS allows it.
    """
    keys_dir = Path(keys_directory) if keys_directory is not None else _default_keys_directory()
    keys_dir.mkdir(parents=True, exist_ok=True)

    private_path = keys_dir / PRIVATE_KEY_NAME
    public_path = keys_dir / PUBLIC_KEY_NAME

    if private_path.is_file() and public_path.is_file():
        return private_path, public_path

    if private_path.is_file() or public_path.is_file():
        raise FileExistsError(
            f"Incomplete keypair: found one of {PRIVATE_KEY_NAME} / {PUBLIC_KEY_NAME} in {keys_dir}"
        )

    private_key = Ed25519PrivateKey.generate()
    priv_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    pub_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    private_path.write_bytes(priv_pem)
    public_path.write_bytes(pub_pem)

    # UNIX: owner read/write only for secret key (best-effort on Windows).
    if os.name != "nt":
        try:
            os.chmod(private_path, stat.S_IRUSR | stat.S_IWUSR)
        except OSError:
            pass

    return private_path, public_path


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _build_pdf(
    output_pdf: Path,
    payload: Mapping[str, Any],
    sha256_hex: str,
    signature_b64: str,
) -> None:
    doc = SimpleDocTemplate(str(output_pdf), pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    title = Paragraph("Data Erasure Certificate", styles["Title"])
    story.append(title)
    story.append(Spacer(1, 18))

    lines = [
        ("Operation type", str(payload.get("operation_type", ""))),
        ("Target path", str(payload.get("target_path", ""))),
        ("Timestamp (ISO)", str(payload.get("timestamp", ""))),
        ("Wipe method", str(payload.get("wipe_method", ""))),
        ("Status", str(payload.get("status", ""))),
        ("Tool", str(payload.get("tool_name", ""))),
        ("Version", str(payload.get("version", ""))),
        ("SHA-256 (canonical JSON)", sha256_hex),
        ("Signature (Base64)", signature_b64),
    ]

    for label, value in lines:
        block = Paragraph(f"<b>{label}:</b> {value}", styles["Normal"])
        story.append(block)
        story.append(Spacer(1, 8))

    statement = Paragraph(
        "<i>This certificate verifies that the specified data has been securely erased.</i>",
        styles["BodyText"],
    )
    story.append(Spacer(1, 12))
    story.append(statement)

    doc.build(story)


def generate_certificate(
    output_dir: Union[str, Path],
    operation_type: str,
    target_path: str,
    wipe_method: str,
    status: str,
    *,
    tool_name: str = DEFAULT_TOOL_NAME,
    version: str | None = None,
    keys_directory: Union[str, Path] | None = None,
) -> dict[str, Any]:
    """
    Write ``certificate.json``, ``signature.sig``, and ``certificate.pdf`` into ``output_dir``.

    ``wipe_method`` should be ``\"1-pass\"`` or ``\"3-pass\"`` (NIST Clear / Purge mapping).

    ``operation_type`` must be one of: ``file_wipe``, ``folder_wipe``, ``free_space``.

    Raises on cryptographic or filesystem errors so callers can catch and log.
    """
    valid_ops = {"file_wipe", "folder_wipe", "free_space"}
    if operation_type not in valid_ops:
        raise ValueError(f"operation_type must be one of {sorted(valid_ops)}")
    if wipe_method not in ("1-pass", "3-pass"):
        raise ValueError('wipe_method must be "1-pass" or "3-pass"')
    if status not in ("success", "failure"):
        raise ValueError('status must be "success" or "failure"')

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    private_key_path, _public_key_path = generate_keys(keys_directory)

    ts = datetime.now(timezone.utc).isoformat()
    payload: dict[str, Any] = {
        "operation_type": operation_type,
        "target_path": target_path,
        "timestamp": ts,
        "wipe_method": wipe_method,
        "status": status,
        "tool_name": tool_name,
        "version": version or __version__,
    }

    canonical_bytes = _canonical_json_bytes(payload)
    sha256_digest = hashlib.sha256(canonical_bytes).digest()
    sha256_hex = sha256_digest.hex()

    signature = sign_data(sha256_digest, private_key_path)
    signature_b64 = base64.b64encode(signature).decode("ascii")

    cert_json_path = out / "certificate.json"
    sig_path = out / "signature.sig"
    pdf_path = out / "certificate.pdf"

    cert_json_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    sig_path.write_bytes(signature)
    _build_pdf(pdf_path, payload, sha256_hex, signature_b64)

    return {
        "certificate_json": str(cert_json_path),
        "signature_sig": str(sig_path),
        "certificate_pdf": str(pdf_path),
        "sha256_hex": sha256_hex,
        "signature_base64": signature_b64,
    }


def verify_certificate(
    certificate_json: Union[str, Path],
    signature_sig: Union[str, Path],
    public_key_pem: Union[str, Path],
) -> bool:
    """
    Recompute SHA-256 over the canonical JSON fields and verify the Ed25519 signature.

    Reads the JSON object from disk, then recomputes the digest/signature pipeline
    using sorted-key canonical JSON (must match generation).
    """
    cert_path = Path(certificate_json)
    sig_path = Path(signature_sig)
    pub_path = Path(public_key_pem)

    try:
        payload = json.loads(cert_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False

    if not isinstance(payload, dict):
        return False

    canonical_bytes = _canonical_json_bytes(payload)
    digest = hashlib.sha256(canonical_bytes).digest()

    try:
        signature = sig_path.read_bytes()
    except OSError:
        return False

    try:
        pub = serialization.load_pem_public_key(pub_path.read_bytes())
    except OSError:
        return False

    if not isinstance(pub, Ed25519PublicKey):
        return False

    try:
        pub.verify(signature, digest)
    except InvalidSignature:
        return False
    except Exception:
        return False

    return True

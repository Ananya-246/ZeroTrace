"""
NIST SP 800-88–oriented file-level sanitization (logical overwrite only).

Scope: user-space overwrite of file bytes. Does not invoke SSD firmware sanitize,
ATA secure erase, or volume-level commands.

Patterns:
  - Clear: single full pass of binary zeros (0x00).
  - Purge (software approximation): 0x00 → os.urandom → 0x00, with fsync per pass.
"""

from __future__ import annotations

import logging
import os
from typing import BinaryIO

_log = logging.getLogger(__name__)

# Chunk size for reads/writes (bounds RAM; full logical size is still covered).
CHUNK_SIZE = 1024 * 1024  # 1 MiB


class NISTAlgorithms:
    """Static helpers for NIST Clear / software Purge-style file overwrites."""

    @staticmethod
    def _log(msg: str) -> None:
        """Console + logger for CLI and service visibility."""
        line = f"    [wipe] {msg}"
        print(line)
        _log.info(msg)

    @staticmethod
    def _write_chunk_exact(f: BinaryIO, data: bytes) -> None:
        """Write buffer in full; raise if the OS short-writes."""
        n = len(data)
        if n == 0:
            return
        written = f.write(data)
        if written != n:
            raise OSError(f"short write: expected {n} bytes, wrote {written}")

    @staticmethod
    def _sync_file(f: BinaryIO, file_size: int) -> None:
        """Push buffers and commit file length after a pass."""
        f.flush()
        os.fsync(f.fileno())
        f.truncate(file_size)

    @staticmethod
    def _write_zeros_pass(f: BinaryIO, file_size: int, pass_label: str) -> int:
        """One full pass of binary zeros from offset 0 through file_size."""
        f.seek(0)
        total = 0
        zeros_block = b"\x00" * CHUNK_SIZE
        while total < file_size:
            n = min(CHUNK_SIZE, file_size - total)
            chunk = zeros_block if n == CHUNK_SIZE else b"\x00" * n
            NISTAlgorithms._write_chunk_exact(f, chunk)
            total += n
        NISTAlgorithms._sync_file(f, file_size)
        NISTAlgorithms._log(f"{pass_label}: wrote {total} bytes (binary 0x00)")
        return total

    @staticmethod
    def _write_random_pass(f: BinaryIO, file_size: int, pass_label: str) -> int:
        """One full pass of cryptographically secure random bytes."""
        f.seek(0)
        total = 0
        while total < file_size:
            n = min(CHUNK_SIZE, file_size - total)
            chunk = os.urandom(n)
            NISTAlgorithms._write_chunk_exact(f, chunk)
            total += n
        NISTAlgorithms._sync_file(f, file_size)
        NISTAlgorithms._log(f"{pass_label}: wrote {total} bytes (os.urandom)")
        return total

    @staticmethod
    def _verify_all_binary_zeros(file_path: str, file_size: int) -> bool:
        """
        Read-back verification: every byte must be 0x00.

        Interprets success as: no residual non-zero content in the user data fork
        after the final zero pass (cannot compare to unknown original without a digest).
        """
        if file_size == 0:
            return True
        with open(file_path, "rb", buffering=0) as f:
            remaining = file_size
            while remaining > 0:
                n = min(CHUNK_SIZE, remaining)
                chunk = f.read(n)
                if len(chunk) != n:
                    return False
                if any(chunk):
                    return False
                remaining -= n
        return True

    @staticmethod
    def clear(file_path: str, verify: bool = True) -> None:
        """
        NIST Clear (file-level): single overwrite pass with true binary zeros.

        ``verify``: if True, re-read entire file and confirm all bytes are 0x00.
        """
        file_size = os.path.getsize(file_path)
        NISTAlgorithms._log(f"NIST Clear start: {file_path} ({file_size} bytes)")

        with open(file_path, "r+b", buffering=0) as f:
            NISTAlgorithms._write_zeros_pass(f, file_size, "pass 1/1 (Clear)")

        if verify:
            if not NISTAlgorithms._verify_all_binary_zeros(file_path, file_size):
                raise OSError(f"Verification failed: not all binary zeros in {file_path}")
            NISTAlgorithms._log("NIST Clear: verification OK — complete")
        else:
            NISTAlgorithms._log("NIST Clear: complete (verify skipped)")

    @staticmethod
    def purge(file_path: str, verify: bool = True) -> None:
        """
        Software-level Purge-style pattern: 0x00 → random → 0x00, full length each time.

        ``verify``: if True, after pass 3 confirm entire file is 0x00.
        """
        file_size = os.path.getsize(file_path)
        NISTAlgorithms._log(f"NIST Purge start: {file_path} ({file_size} bytes)")

        with open(file_path, "r+b", buffering=0) as f:
            NISTAlgorithms._write_zeros_pass(f, file_size, "pass 1/3 (Purge, 0x00)")
            NISTAlgorithms._write_random_pass(f, file_size, "pass 2/3 (Purge, random)")
            NISTAlgorithms._write_zeros_pass(f, file_size, "pass 3/3 (Purge, 0x00)")

        if verify:
            if not NISTAlgorithms._verify_all_binary_zeros(file_path, file_size):
                raise OSError(f"Verification failed: not all binary zeros in {file_path}")
            NISTAlgorithms._log("NIST Purge: verification OK — complete")
        else:
            NISTAlgorithms._log("NIST Purge: complete (verify skipped)")

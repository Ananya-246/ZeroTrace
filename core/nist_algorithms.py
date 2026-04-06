"""
NIST-based wiping algorithms.
Implements Clear and Purge methods with verification.
"""
import os
import struct

class NISTAlgorithms:

    @staticmethod
    def _write_and_sync(f, data: bytes, file_size: int):
        """Helper: write, flush, and fsync a full pass."""
        f.seek(0)
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
        f.truncate(file_size)   # prevent file growth on some FS

    @staticmethod
    def _verify_pass(f, expected_byte: bytes, file_size: int) -> bool:
        """Read back and confirm every byte matches expected."""
        f.seek(0)
        chunk_size = 65536  # 64KB chunks avoids loading huge files into RAM
        verified = 0
        while verified < file_size:
            chunk = f.read(min(chunk_size, file_size - verified))
            if not chunk:
                break
            if chunk != expected_byte * len(chunk):
                return False
            verified += len(chunk)
        return True

    @staticmethod
    def clear(file_path: str, verify: bool = True):
        """
        NIST Clear:
        Single overwrite pass with zeros + optional verification.
        """
        file_size = os.path.getsize(file_path)
        zeros = b"0" * file_size

        with open(file_path, "r+b", buffering=0) as f:  # buffering=0 = unbuffered I/O
            NISTAlgorithms._write_and_sync(f, zeros, file_size)

            if verify and not NISTAlgorithms._verify_pass(f, b"0", file_size):
                raise IOError(f"Verification failed: zeros not confirmed in {file_path}")

    @staticmethod
    def purge(file_path: str, verify: bool = True):
        """
        NIST Purge:
        3-pass overwrite:
          1. Zeros
          2. Random data
          3. Zeros + verification
        """
        file_size = os.path.getsize(file_path)

        with open(file_path, "r+b", buffering=0) as f:  # unbuffered
            # Pass 1: Zeros
            NISTAlgorithms._write_and_sync(f, b"0" * file_size, file_size)

            # Pass 2: Cryptographically secure random data
            NISTAlgorithms._write_and_sync(f, os.urandom(file_size), file_size)

            # Pass 3: Zeros
            NISTAlgorithms._write_and_sync(f, b"0" * file_size, file_size)

            # Verify final pass
            if verify and not NISTAlgorithms._verify_pass(f, b"0", file_size):
                raise IOError(f"Verification failed: zeros not confirmed in {file_path}")
"""
NIST-based wiping algorithms.
Implements Clear and Purge methods.
"""

import os
import random


class NISTAlgorithms:

    @staticmethod
    def clear(file_path: str):
        """
        NIST Clear:
        Single overwrite pass with zeros.
        """
        file_size = os.path.getsize(file_path)

        with open(file_path, "r+b") as f:
            f.seek(0)
            f.write(b"\x00" * file_size)
            f.flush()
            os.fsync(f.fileno())

    @staticmethod
    def purge(file_path: str):
        """
        NIST Purge:
        3-pass overwrite:
        1. Zeros
        2. Random data
        3. Zeros
        """
        file_size = os.path.getsize(file_path)

        with open(file_path, "r+b") as f:
            # Pass 1: Zeros
            f.seek(0)
            f.write(b"\x00" * file_size)
            f.flush()
            os.fsync(f.fileno())

            # Pass 2: Random
            f.seek(0)
            random_data = os.urandom(file_size)
            f.write(random_data)
            f.flush()
            os.fsync(f.fileno())

            # Pass 3: Zeros
            f.seek(0)
            f.write(b"\x00" * file_size)
            f.flush()
            os.fsync(f.fileno())


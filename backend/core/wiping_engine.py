# import os

# class WipingEngine:

#     def secure_wipe_file(self, path, passes=3):
#         try:
#             length = os.path.getsize(path)

#             with open(path, "r+b") as f:
#                 for _ in range(passes):
#                     f.seek(0)
#                     f.write(os.urandom(length))
#                     f.flush()

#                 # Final zero pass
#                 f.seek(0)
#                 f.write(b"\x00" * length)
#                 f.flush()

#             os.remove(path)

#         except Exception as e:
#             raise e

from __future__ import annotations

import errno
import os
import secrets
import shutil
from pathlib import Path

from core.nist_algorithms import CHUNK_SIZE, NISTAlgorithms


class WipingEngine:
    # ---------------------------
    # SECURE WIPE + DELETE
    # ---------------------------

    @staticmethod
    def _random_filename_32hex() -> str:
        """32 hex characters (16 bytes); no predictable prefix."""
        return secrets.token_hex(16)

    @staticmethod
    def _pick_unique_random_path(parent: Path) -> Path:
        for _ in range(64):
            candidate = parent / WipingEngine._random_filename_32hex()
            if not candidate.exists():
                return candidate
        raise OSError("could not allocate a unique random filename")

    @staticmethod
    def free_space_wipe_volume(directory: Path) -> None:
        """
        Optional slack-space scrub: append random data to a temp file until the
        volume is nearly full, then remove it. Uses 1 MiB chunks and ``os.urandom``.

        ``directory`` must be on the volume to scrub (typically a folder root or
        a file's parent). Leaves ``RESERVE_FREE`` bytes free to avoid destabilizing
        the host OS.
        """
        reserve_free = 128 * 1024 * 1024  # 128 MiB
        d = directory.resolve()
        if d.is_file():
            d = d.parent
        if not d.is_dir():
            raise NotADirectoryError(f"not a directory: {directory}")

        tmp = WipingEngine._pick_unique_random_path(d)
        written = 0
        print(f"    [wipe] free-space wipe: volume of {d} (temp {tmp.name})")

        try:
            with open(tmp, "ab", buffering=0) as f:
                while True:
                    usage = shutil.disk_usage(str(d))
                    if usage.free <= reserve_free:
                        break
                    to_write = min(CHUNK_SIZE, usage.free - reserve_free)
                    if to_write < 4096:
                        break
                    buf = os.urandom(to_write)
                    w = f.write(buf)
                    if w != to_write:
                        raise OSError(f"short write during free-space wipe ({w} != {to_write})")
                    f.flush()
                    os.fsync(f.fileno())
                    written += w
        except OSError as exc:
            if exc.errno not in (errno.ENOSPC, errno.EDQUOT):
                # Windows often reports ERROR_DISK_FULL (112) instead of errno.ENOSPC.
                if getattr(exc, "winerror", None) not in (112,):
                    raise
        finally:
            try:
                if tmp.exists():
                    tmp.unlink()
            except OSError:
                pass

        print(f"    [wipe] free-space wipe complete (~{written} bytes written, temp removed)")

    def secure_wipe_file(
        self,
        path,
        method: str = "purge",
        *,
        use_hidden_staging: bool = False,
    ):
        """
        Obfuscate path → overwrite → unlink.

        **Default (``use_hidden_staging=False``):** ``os.replace`` into the same
        directory with a **32-hex** random name (``secrets.token_hex(16)``), then
        NIST passes, then ``os.remove``.

        **Optional (``use_hidden_staging=True``):** create a **hidden-style**
        subdirectory under the file's parent (name ``.<hex>``), move the file
        inside with a random hex name, wipe there, delete, then remove the empty
        staging directory — breaks linkage to the original directory entry before
        overwrite.

        Logs original path, final work path, deletion, and whether the original
        path still exists (expected **False** for a wiped **file**).
        """
        path_str = os.fspath(path)
        p = Path(path_str)
        try:
            p = p.resolve()
        except OSError:
            p = Path(path_str).absolute()

        if not p.is_file():
            raise FileNotFoundError(f"not a file or missing: {path_str}")

        original_abs = str(p)
        original_name = p.name
        parent = p.parent
        staging_dir: Path | None = None
        work_path: Path

        print(f"    [wipe] original path: {original_abs}")

        try:
            if use_hidden_staging:
                staging_dir = parent / f".{secrets.token_hex(12)}"
                staging_dir.mkdir(mode=0o700, exist_ok=False)
                work_path = staging_dir / self._random_filename_32hex()
                os.replace(str(p), str(work_path))
                print(
                    f"    [wipe] moved to hidden staging: {staging_dir.name}/"
                    f"{work_path.name} (final temp path for wipe)"
                )
            else:
                work_path = self._pick_unique_random_path(parent)
                os.replace(str(p), str(work_path))
                print(
                    f"    [wipe] pre-wipe rename: {original_name} → {work_path.name} "
                    f"(same directory; final temp path for wipe)"
                )
        except OSError as exc:
            if staging_dir is not None and staging_dir.exists():
                try:
                    staging_dir.rmdir()
                except OSError:
                    pass
            raise RuntimeError(f"pre-wipe relocate failed: {exc}") from exc

        work_str = str(work_path)
        try:
            if method == "clear":
                print("    ⏳ NIST Clear — single pass, binary 0x00 (chunked)...")
                NISTAlgorithms.clear(work_str, verify=True)
                print("    ✔ NIST Clear complete.")
            elif method == "purge":
                print("    ⏳ NIST Purge — 3-pass chunked (0x00 → random → 0x00)...")
                NISTAlgorithms.purge(work_str, verify=True)
                print("    ✔ NIST Purge complete.")
            else:
                raise ValueError(f"unknown wipe method: {method!r}")

            os.remove(work_str)
            print(f"    [wipe] deletion confirmed: removed {work_path.name}")
            if staging_dir is not None:
                try:
                    staging_dir.rmdir()
                    print(f"    [wipe] staging directory removed: {staging_dir}")
                except OSError as exc:
                    print(f"    [wipe] staging directory cleanup: {exc}")

            orig_still_there = os.path.exists(original_abs)
            print(
                f"    [wipe] directory entry / path check: original path exists = "
                f"{orig_still_there} (expected False for a deleted file)"
            )
            if not orig_still_there:
                print("    [wipe] directory entry removed: original path no longer exists")
        except Exception:
            raise

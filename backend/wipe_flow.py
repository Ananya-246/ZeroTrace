"""
Shared wipe orchestration matching ``main.py`` CLI behavior.

Used by the HTTP API (and optionally the CLI) so desktop UI and terminal stay aligned.
"""

from __future__ import annotations

import os
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional

from certificate_manager import __version__ as certificate_tool_version
from certificate_manager import generate_certificate
from core.file_scanner import FileScanner
from core.nist_algorithms import NISTAlgorithms
from core.wiping_engine import WipingEngine
from utils.logging import Logger


def get_tool_root() -> Path:
    """Same as CLI: repo root (parent of ``backend``)."""
    return Path(__file__).resolve().parents[1]


def safety_check_blocks_wipe(selected_item: Path) -> Optional[str]:
    """
    Returns an error message if wipe must not proceed, else ``None``.
    Mirrors ``main.py`` safety checks.
    """
    tool_root = get_tool_root()
    try:
        if tool_root in selected_item.resolve().parents or selected_item == tool_root:
            return "Cannot wipe tool directory."
    except Exception:
        pass

    if str(selected_item) in ["/", "C:\\"]:
        return "Cannot wipe system root."

    return None


def list_directory_entries(path: Path) -> list[dict[str, Any]]:
    """
    Children of ``path`` sorted like CLI: folders first, then files, name case-insensitive.
    """
    items = list(path.iterdir())
    items.sort(key=lambda x: (x.is_file(), x.name.lower()))
    out: list[dict[str, Any]] = []
    for item in items:
        out.append(
            {
                "name": item.name,
                "path": str(item),
                "is_directory": item.is_dir(),
                "is_file": item.is_file(),
            }
        )
    return out


def count_wipe_files(selected_item: Path) -> int:
    """Number of files that would be wiped (0 for missing path handled by caller)."""
    if selected_item.is_file():
        return 1
    return len(FileScanner.recursive_files(selected_item))


@dataclass
class DestructiveWipeResult:
    total: int
    passed: int
    failed: int
    certificate: Optional[dict[str, Any]] = None
    certificate_error: Optional[str] = None
    demonstration: Optional[dict[str, Any]] = None


ProgressCallback = Callable[[int, int, str], None]
"""current_index (0-based), total_files, current_file_path"""


def run_destructive_wipe(
    selected_item: Path,
    wipe_method: str,
    logger: Optional[Logger] = None,
    on_progress: Optional[ProgressCallback] = None,
    *,
    free_space_wipe: bool = False,
    use_hidden_staging: bool = False,
) -> DestructiveWipeResult:
    """
    ``wipe_method`` is ``\"clear\"`` or ``\"purge\"`` (same as CLI after choice).

    Performs file collection, per-file ``secure_wipe_file``, summary logging,
    and certificate generation when fully successful — same order as ``main.py``.

    ``free_space_wipe``: when True and the wipe completes with no failures, runs
    one optional slack-space pass on the volume containing ``selected_item``
    (see ``WipingEngine.free_space_wipe_volume``). Default False preserves prior
    call-site behavior.

    ``use_hidden_staging``: passed to ``secure_wipe_file`` (optional hidden staging
    directory before overwrite). Default False.
    """
    if wipe_method not in ("clear", "purge"):
        raise ValueError('wipe_method must be "clear" or "purge"')

    block = safety_check_blocks_wipe(selected_item)
    if block:
        raise RuntimeError(block)

    logger = logger or Logger()
    wiping_engine = WipingEngine()

    was_file = selected_item.is_file()
    try:
        target_path_for_cert = str(selected_item.resolve())
    except Exception:
        target_path_for_cert = str(selected_item)

    if was_file:
        files = [selected_item]
    else:
        files = FileScanner.recursive_files(selected_item)

    passed = 0
    failed = 0
    total = len(files)

    for idx, file in enumerate(files):
        if on_progress:
            on_progress(idx, total, str(file))
        try:
            wiping_engine.secure_wipe_file(
                file,
                method=wipe_method,
                use_hidden_staging=use_hidden_staging,
            )
            passed += 1
            logger.log_info(f"Wiped: {file}")
        except Exception as e:
            print(f"❌ Error: {file} -> {e}")
            logger.log_error(f"{file} -> {e}")
            failed += 1

    if free_space_wipe and failed == 0 and passed > 0:
        scrub_root = selected_item if selected_item.is_dir() else selected_item.parent
        try:
            WipingEngine.free_space_wipe_volume(scrub_root)
            logger.log_info(f"Free-space wipe completed for volume of {scrub_root}")
        except Exception as exc:
            print(f"⚠ Free-space wipe failed: {exc}")
            logger.log_error(f"Free-space wipe: {exc}")

    cert: Optional[dict[str, Any]] = None
    cert_err: Optional[str] = None

    if failed == 0 and passed > 0:
        try:
            stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            cert_dir = (
                Path(__file__).resolve().parent
                / "certificates"
                / f"{stamp}_{uuid.uuid4().hex[:8]}"
            )
            operation_type = "file_wipe" if was_file else "folder_wipe"
            wipe_method_label = "1-pass" if wipe_method == "clear" else "3-pass"
            cert = generate_certificate(
                cert_dir,
                operation_type=operation_type,
                target_path=target_path_for_cert,
                wipe_method=wipe_method_label,
                status="success",
                tool_name="ZeroTrace",
                version=certificate_tool_version,
            )
            logger.log_info(f"Certificate bundle: {cert_dir}")
        except Exception as cert_err_exc:
            cert_err = str(cert_err_exc)
            logger.log_error(f"Certificate generation: {cert_err}")

    if on_progress and total > 0:
        on_progress(total, total, "")

    try:
        anchor_still_exists = os.path.exists(target_path_for_cert)
    except OSError:
        anchor_still_exists = False

    demonstration: dict[str, Any] = {
        "original_target_path": target_path_for_cert,
        "path_exists_after_wipe": anchor_still_exists,
        "target_was_file": was_file,
    }

    return DestructiveWipeResult(
        total=total,
        passed=passed,
        failed=failed,
        certificate=cert,
        certificate_error=cert_err,
        demonstration=demonstration,
    )


def run_overwrite_only(
    selected_file: Path,
    method_choice: str,
    logger: Optional[Logger] = None,
) -> None:
    """
    ``method_choice`` is ``\"1\"`` (NIST Clear) or ``\"2\"`` (NIST Purge), same as CLI.
    """
    if method_choice not in ("1", "2"):
        raise ValueError('method_choice must be "1" or "2"')

    if not selected_file.is_file():
        raise ValueError("Overwrite only applies to a file path")

    logger = logger or Logger()

    if method_choice == "1":
        NISTAlgorithms.clear(str(selected_file), verify=True)
    else:
        NISTAlgorithms.purge(str(selected_file), verify=True)

    logger.log_info(f"Overwrite: {selected_file}")

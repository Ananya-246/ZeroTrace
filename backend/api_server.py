"""
HTTP API for ZeroTrace desktop UI.

Mirrors ``main.py`` flows: drives, browse, destructive wipe (file/folder),
overwrite-only, and progress via background jobs.
"""

from __future__ import annotations

import threading
import uuid
from pathlib import Path
from typing import Any, Optional

import os
from fastapi import BackgroundTasks, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from core.device_discovery import DeviceDiscovery
from wipe_flow import (
    count_wipe_files,
    list_directory_entries,
    run_destructive_wipe,
    run_overwrite_only,
    safety_check_blocks_wipe,
)

app = FastAPI(title="ZeroTrace API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_jobs: dict[str, dict[str, Any]] = {}
_jobs_lock = threading.Lock()


def _job_new() -> str:
    jid = str(uuid.uuid4())
    with _jobs_lock:
        _jobs[jid] = {
            "status": "queued",
            "index": 0,
            "total": 0,
            "current_file": "",
            "result": None,
            "error": None,
        }
    return jid


def _job_update(jid: str, **kwargs: Any) -> None:
    with _jobs_lock:
        if jid in _jobs:
            _jobs[jid].update(kwargs)


def _job_get(jid: str) -> Optional[dict[str, Any]]:
    with _jobs_lock:
        j = _jobs.get(jid)
        return dict(j) if j else None


# ---------------------------------------------------------------------------
# Health / discovery
# ---------------------------------------------------------------------------


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/drives")
def api_drives() -> dict[str, list[str]]:
    drives = DeviceDiscovery.list_drives()
    return {"drives": [str(d) for d in drives]}


@app.get("/api/browse")
def api_browse(path: str = Query(..., description="Absolute directory path")) -> dict[str, Any]:
    p = Path(path)
    if not p.exists():
        raise HTTPException(status_code=400, detail="Path does not exist")
    if not p.is_dir():
        raise HTTPException(status_code=400, detail="Not a directory")
    try:
        entries = list_directory_entries(p)
    except PermissionError:
        raise HTTPException(status_code=403, detail="Access denied")
    try:
        resolved = str(p.resolve())
    except Exception:
        resolved = str(p)
    parent = p.parent
    try:
        parent_s = str(parent.resolve()) if parent != p else resolved
    except Exception:
        parent_s = str(parent)
    return {"current_path": resolved, "parent_path": parent_s, "entries": entries}


@app.get("/api/file-count")
def api_file_count(path: str = Query(...)) -> dict[str, int]:
    p = Path(path)
    if not p.exists():
        raise HTTPException(status_code=400, detail="Path does not exist")
    msg = safety_check_blocks_wipe(p)
    if msg:
        raise HTTPException(status_code=400, detail=msg)
    return {"count": count_wipe_files(p)}


@app.get("/api/file-size")
def api_file_size(path: str = Query(...)) -> dict[str, int]:
    p = Path(path)
    if not p.is_file():
        raise HTTPException(status_code=400, detail="Not a file")
    return {"size": int(os.path.getsize(p))}


@app.get("/api/path-exists")
def api_path_exists(path: str = Query(..., description="Path to test with os.path.exists")) -> dict[str, Any]:
    """Return whether ``path`` currently exists (for UI / demo verification)."""
    try:
        exists = os.path.exists(path)
    except (OSError, ValueError):
        exists = False
    return {"exists": bool(exists), "path": path}


# ---------------------------------------------------------------------------
# Wipe jobs
# ---------------------------------------------------------------------------


class WipeRequest(BaseModel):
    path: str = Field(..., description="Absolute path to file or folder")
    method: str = Field(..., description='NIST method: "clear" or "purge"')
    use_hidden_staging: bool = Field(
        default=False,
        description="If true, move each file into a hidden staging dir before wipe",
    )


def _normalize_method(method: str) -> str:
    m = method.strip().lower()
    if m not in ("clear", "purge"):
        raise HTTPException(status_code=400, detail='method must be "clear" or "purge"')
    return m


def _run_destructive_job(
    job_id: str,
    path: Path,
    method: str,
    use_hidden_staging: bool = False,
) -> None:
    _job_update(job_id, status="running")

    def on_progress(idx: int, total: int, current: str) -> None:
        _job_update(
            job_id,
            index=idx,
            total=total,
            current_file=current,
        )

    try:
        result = run_destructive_wipe(
            path,
            method,
            on_progress=on_progress,
            use_hidden_staging=use_hidden_staging,
        )
        success = result.failed == 0 and result.passed > 0
        _job_update(
            job_id,
            status="completed",
            result={
                "success": success,
                "total": result.total,
                "passed": result.passed,
                "failed": result.failed,
                "certificate": result.certificate,
                "certificate_error": result.certificate_error,
                "demonstration": result.demonstration,
            },
        )
    except Exception as e:
        _job_update(job_id, status="failed", error=str(e))


def _run_overwrite_job(job_id: str, path: Path, method: str) -> None:
    _job_update(job_id, status="running", index=0, total=1, current_file=str(path))
    try:
        anchor = str(path.resolve())
    except OSError:
        anchor = str(path)
    try:
        choice = "1" if method == "clear" else "2"
        run_overwrite_only(path, choice)
        try:
            still = os.path.exists(anchor)
        except OSError:
            still = True
        _job_update(
            job_id,
            status="completed",
            index=1,
            total=1,
            current_file="",
            result={
                "success": True,
                "total": 1,
                "passed": 1,
                "failed": 0,
                "certificate": None,
                "certificate_error": None,
                "demonstration": {
                    "original_target_path": anchor,
                    "path_exists_after_wipe": still,
                    "target_was_file": True,
                    "overwrite_only": True,
                },
            },
        )
    except Exception as e:
        _job_update(job_id, status="failed", error=str(e))


@app.post("/wipe/file")
def wipe_file(body: WipeRequest, background_tasks: BackgroundTasks) -> dict[str, str]:
    method = _normalize_method(body.method)
    p = Path(body.path)
    if not p.is_file():
        raise HTTPException(status_code=400, detail="Path must be an existing file")
    msg = safety_check_blocks_wipe(p)
    if msg:
        raise HTTPException(status_code=400, detail=msg)
    jid = _job_new()
    background_tasks.add_task(
        _run_destructive_job,
        jid,
        p,
        method,
        body.use_hidden_staging,
    )
    return {"job_id": jid}


@app.post("/wipe/folder")
def wipe_folder(body: WipeRequest, background_tasks: BackgroundTasks) -> dict[str, str]:
    method = _normalize_method(body.method)
    p = Path(body.path)
    if not p.is_dir():
        raise HTTPException(status_code=400, detail="Path must be an existing directory")
    msg = safety_check_blocks_wipe(p)
    if msg:
        raise HTTPException(status_code=400, detail=msg)
    jid = _job_new()
    background_tasks.add_task(
        _run_destructive_job,
        jid,
        p,
        method,
        body.use_hidden_staging,
    )
    return {"job_id": jid}


@app.post("/wipe/overwrite")
def wipe_overwrite(body: WipeRequest, background_tasks: BackgroundTasks) -> dict[str, str]:
    method = _normalize_method(body.method)
    p = Path(body.path)
    if not p.is_file():
        raise HTTPException(status_code=400, detail="Path must be an existing file")
    jid = _job_new()
    background_tasks.add_task(_run_overwrite_job, jid, p, method)
    return {"job_id": jid}


@app.get("/wipe/jobs/{job_id}")
def wipe_job_status(job_id: str) -> dict[str, Any]:
    j = _job_get(job_id)
    if not j:
        raise HTTPException(status_code=404, detail="Unknown job_id")
    return {"job_id": job_id, **j}


def main() -> None:
    import uvicorn

    uvicorn.run("api_server:app", host="127.0.0.1", port=8765, reload=False)


if __name__ == "__main__":
    main()

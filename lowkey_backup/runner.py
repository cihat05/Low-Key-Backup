from __future__ import annotations
from pathlib import Path
from datetime import datetime
import shlex, subprocess, shutil

from .config import LOG_DIR
from .db import connect

def _ts():
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

def _log(job: str, msg: str):
    p = Path(LOG_DIR) / f"{job}.log"
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(msg + "\n")

def _run(cmd: list[str], job: str):
    _log(job, "CMD: " + " ".join(shlex.quote(c) for c in cmd))
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    while True:
        line = proc.stdout.readline()
        if not line and proc.poll() is not None:
            break
        if line:
            _log(job, line.rstrip("\n"))
    rc = proc.wait()
    if rc != 0:
        raise RuntimeError(f"command failed rc={rc}")

def _latest(base: Path):
    p = base / "latest"
    return str(p.resolve()) if p.exists() else None

def _set_latest(base: Path, target: Path):
    p = base / "latest"
    try:
        if p.exists() or p.is_symlink():
            p.unlink()
    except FileNotFoundError:
        pass
    p.symlink_to(target, target_is_directory=True)

def _apply_keep(base: Path, keep: str):
    if keep == "ALL":
        return
    try:
        n = int(keep)
    except ValueError:
        return
    snaps = [p for p in base.iterdir() if p.is_dir() and p.name != "latest"]
    snaps.sort(key=lambda x: x.name)
    if len(snaps) > n:
        for p in snaps[:len(snaps)-n]:
            shutil.rmtree(p, ignore_errors=True)

def run_job(job_id: int):
    with connect() as conn:
        row = conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
        if not row:
            raise RuntimeError("Job not found")
        job = dict(row)
        started = datetime.now().isoformat()
        run_id = conn.execute("INSERT INTO runs (job_id, started_at, status) VALUES (?,?,?)",
                              (job_id, started, "RUNNING")).lastrowid
        conn.commit()

    name = job["name"]
    try:
        _log(name, f"=== {datetime.now().isoformat()} {job['type']} ===")

        root = Path(job["dst_path"]) / name
        typedir = root / job["type"]
        snap = typedir / _ts()
        snap.mkdir(parents=True, exist_ok=True)

        # if INCR but no latest -> FULL first
        link_dest = _latest(typedir) if job["type"] == "INCR" else None
        if job["type"] == "INCR" and not link_dest:
            job["type"] = "FULL"
            typedir = root / "FULL"
            snap = typedir / _ts()
            snap.mkdir(parents=True, exist_ok=True)
            link_dest = None

        # rsync (local receiver)
        ssh = ["ssh", "-p", str(job["src_port"])]
        if job["src_auth_type"] == "key" and job["src_key_path"]:
            ssh += ["-i", job["src_key_path"]]
        prefix = []
        if job["src_auth_type"] == "password" and job["src_password"]:
            prefix = ["sshpass", "-p", job["src_password"]]

        src_path = job["src_path"]
        if not src_path.endswith("/"):
            src_path += "/"

        cmd = prefix + ["rsync", "-aHAX", "--numeric-ids", "--delete"]
        if link_dest:
            cmd += ["--link-dest", link_dest]
        cmd += ["-e", " ".join(shlex.quote(x) for x in ssh),
                f"{job['src_user']}@{job['src_host']}:{src_path}",
                str(snap) + "/"]

        _run(cmd, name)
        _set_latest(typedir, snap)
        _apply_keep(typedir, job["keep"])

        finished = datetime.now().isoformat()
        with connect() as conn:
            conn.execute("UPDATE runs SET finished_at=?, status=?, message=? WHERE id=?",
                         (finished, "OK", "done", run_id))
            conn.execute("UPDATE jobs SET last_run=?, updated_at=? WHERE id=?",
                         (finished, finished, job_id))
            conn.commit()
    except Exception as e:
        finished = datetime.now().isoformat()
        with connect() as conn:
            conn.execute("UPDATE runs SET finished_at=?, status=?, message=? WHERE id=?",
                         (finished, "ERROR", str(e), run_id))
            conn.commit()
        _log(name, "ERROR: " + str(e))
        raise

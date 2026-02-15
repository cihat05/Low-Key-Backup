from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from datetime import datetime, timezone

from .db import init_db, connect
from .models import SSHTestRequest, SSHBrowseRequest, JobCreate, JobUpdate
from .sshutils import test_ssh, list_dir
from .scheduler import JobScheduler

app = FastAPI(title="Low-Key Backup")
web_dir = Path(__file__).resolve().parent / "web"
app.mount("/static", StaticFiles(directory=web_dir), name="static")

sched = JobScheduler()

def _now():
    return datetime.now(timezone.utc).isoformat()

@app.on_event("startup")
def startup():
    init_db()
    sched.start()

@app.on_event("shutdown")
def shutdown():
    sched.shutdown()

@app.get("/", response_class=HTMLResponse)
def index():
    return (web_dir / "index.html").read_text(encoding="utf-8")

@app.post("/api/ssh/test")
def ssh_test(req: SSHTestRequest):
    try:
        test_ssh(req.host, req.port, req.user, req.auth_type, req.key_path, req.password)
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/ssh/browse")
def ssh_browse(req: SSHBrowseRequest):
    try:
        items = list_dir(req.host, req.port, req.user, req.auth_type, req.key_path, req.password, req.path)
        return {"path": req.path, "items": items}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/jobs")
def jobs_list():
    with connect() as conn:
        rows = conn.execute("SELECT * FROM jobs ORDER BY name").fetchall()
        return [dict(r) for r in rows]

@app.post("/api/jobs")
def jobs_create(job: JobCreate):
    ts = _now()
    days = ",".join(job.days)
    with connect() as conn:
        try:
            conn.execute(
                """INSERT INTO jobs (
                  name, src_host, src_port, src_user, src_auth_type, src_key_path, src_password, src_path,
                  dst_host, dst_port, dst_user, dst_auth_type, dst_key_path, dst_password, dst_path,
                  days, time_hhmm, keep, type, created_at, updated_at
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    job.name, job.src_host, job.src_port, job.src_user, job.src_auth_type, job.src_key_path, job.src_password, job.src_path,
                    job.dst_host, job.dst_port, job.dst_user, job.dst_auth_type, job.dst_key_path, job.dst_password, job.dst_path,
                    days, job.time_hhmm, job.keep, job.type, ts, ts
                )
            )
            conn.commit()
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
    sched.reload()
    return {"ok": True}

@app.put("/api/jobs/{job_id}")
def jobs_update(job_id: int, job: JobUpdate):
    ts = _now()
    days = ",".join(job.days)
    with connect() as conn:
        if not conn.execute("SELECT id FROM jobs WHERE id=?", (job_id,)).fetchone():
            raise HTTPException(status_code=404, detail="Job nicht gefunden")
        try:
            conn.execute(
                """UPDATE jobs SET
                  name=?, src_host=?, src_port=?, src_user=?, src_auth_type=?, src_key_path=?, src_password=?, src_path=?,
                  dst_host=?, dst_port=?, dst_user=?, dst_auth_type=?, dst_key_path=?, dst_password=?, dst_path=?,
                  days=?, time_hhmm=?, keep=?, type=?, updated_at=?
                WHERE id=?""",
                (
                    job.name, job.src_host, job.src_port, job.src_user, job.src_auth_type, job.src_key_path, job.src_password, job.src_path,
                    job.dst_host, job.dst_port, job.dst_user, job.dst_auth_type, job.dst_key_path, job.dst_password, job.dst_path,
                    days, job.time_hhmm, job.keep, job.type, ts, job_id
                )
            )
            conn.commit()
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
    sched.reload()
    return {"ok": True}

@app.delete("/api/jobs/{job_id}")
def jobs_delete(job_id: int):
    with connect() as conn:
        if not conn.execute("SELECT id FROM jobs WHERE id=?", (job_id,)).fetchone():
            raise HTTPException(status_code=404, detail="Job nicht gefunden")
        conn.execute("DELETE FROM jobs WHERE id=?", (job_id,))
        conn.commit()
    sched.reload()
    return {"ok": True}

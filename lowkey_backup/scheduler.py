from __future__ import annotations
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import threading
from .db import connect
from .runner import run_job

DOW_MAP = {"MO":"mon","TU":"tue","WE":"wed","TH":"thu","FR":"fri","SA":"sat","SO":"sun"}

class JobScheduler:
    def __init__(self):
        self.sched = BackgroundScheduler(timezone="UTC")
        self._lock = threading.Lock()

    def start(self):
        self.sched.start()
        self.reload()

    def shutdown(self):
        self.sched.shutdown(wait=False)

    def reload(self):
        with self._lock:
            self.sched.remove_all_jobs()
            with connect() as conn:
                rows = conn.execute("SELECT id, days, time_hhmm FROM jobs").fetchall()
            for r in rows:
                job_id = int(r["id"])
                days = [d for d in (r["days"] or "").split(",") if d]
                hh, mm = (r["time_hhmm"] or "00:00").split(":")
                dow = ",".join(DOW_MAP[d] for d in days if d in DOW_MAP)
                if not dow:
                    continue
                trig = CronTrigger(day_of_week=dow, hour=int(hh), minute=int(mm))
                self.sched.add_job(run_job, trig, args=[job_id], id=f"job-{job_id}", replace_existing=True)

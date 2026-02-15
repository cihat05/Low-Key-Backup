from __future__ import annotations
import stat
from typing import List, Dict
import paramiko

def _connect(host: str, port: int, user: str, auth_type: str, key_path: str | None, password: str | None) -> paramiko.SSHClient:
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    if auth_type == "key":
        if key_path:
            c.connect(hostname=host, port=port, username=user, key_filename=key_path, timeout=10)
        else:
            c.connect(hostname=host, port=port, username=user, timeout=10)
    else:
        if password is None:
            raise ValueError("password fehlt")
        c.connect(hostname=host, port=port, username=user, password=password, timeout=10)
    return c

def test_ssh(host: str, port: int, user: str, auth_type: str, key_path: str | None, password: str | None) -> None:
    c = _connect(host, port, user, auth_type, key_path, password)
    c.close()

def list_dir(host: str, port: int, user: str, auth_type: str, key_path: str | None, password: str | None, path: str) -> List[Dict]:
    if not path:
        path = "/"
    c = _connect(host, port, user, auth_type, key_path, password)
    try:
        sftp = c.open_sftp()
        try:
            out = []
            for attr in sftp.listdir_attr(path):
                out.append({"name": attr.filename, "is_dir": stat.S_ISDIR(attr.st_mode)})
            out.sort(key=lambda x: (not x["is_dir"], x["name"].lower()))
            return out
        finally:
            sftp.close()
    finally:
        c.close()

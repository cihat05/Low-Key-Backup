from pydantic import BaseModel, Field
from typing import Optional, Literal, List

AuthType = Literal["key", "password"]
JobType = Literal["FULL", "INCR"]
Day = Literal["MO","TU","WE","TH","FR","SA","SO"]

class SSHTestRequest(BaseModel):
    host: str
    port: int = 22
    user: str
    auth_type: AuthType = "key"
    key_path: Optional[str] = None
    password: Optional[str] = None

class SSHBrowseRequest(SSHTestRequest):
    path: str = "/"

class JobCreate(BaseModel):
    name: str = Field(min_length=1, max_length=64)

    src_host: str
    src_port: int = 22
    src_user: str
    src_auth_type: AuthType = "key"
    src_key_path: Optional[str] = None
    src_password: Optional[str] = None
    src_path: str

    dst_host: str
    dst_port: int = 22
    dst_user: str
    dst_auth_type: AuthType = "key"
    dst_key_path: Optional[str] = None
    dst_password: Optional[str] = None
    dst_path: str

    days: List[Day]
    time_hhmm: str
    keep: str
    type: JobType

class JobUpdate(JobCreate):
    pass

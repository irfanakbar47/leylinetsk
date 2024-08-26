from pydantic import BaseModel
from typing import List

class LookupRequest(BaseModel):
    domain: str

class LookupResponse(BaseModel):
    domain: str
    ipv4_addresses: List[str]

class QueryLogResponse(BaseModel):
    id: int
    domain: str
    ip_address: str
    query_time: str  # ISO 8601 format

class HistoryResponse(BaseModel):
    history: List[QueryLogResponse]

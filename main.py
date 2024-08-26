from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, validator
import ipaddress
import socket
import os
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List
from datetime import datetime
import time
import yaml
from schemas import LookupRequest, LookupResponse, QueryLogResponse, HistoryResponse
from prometheus_fastapi_instrumentator import Instrumentator

# Initialize FastAPI
app = FastAPI()

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "postgres://myuser:mypassword@postgres/lookup_service")

def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

def wait_for_db():
    while True:
        try:
            conn = get_db_connection()
            conn.close()
            break
        except psycopg2.OperationalError:
            time.sleep(2)

@app.on_event("startup")
async def startup_event():
    wait_for_db()

# Root endpoint
@app.get("/", response_model=dict)
async def root():
    current_time = int(datetime.utcnow().timestamp())
    is_kubernetes = os.getenv("KUBERNETES_SERVICE_HOST") is not None
    return {
        "date": current_time,
        "version": "1.0.0",
        "kubernetes": is_kubernetes
    }

# Health check endpoint
@app.get("/health", response_model=dict)
async def health_check():
    return {"status": "healthy"}

# IPv4 Validation Model
class IPv4ValidateRequest(BaseModel):
    ip_address: str  # Field name to match the request body

    @validator('ip_address')
    def validate_ip_address(cls, v):
        try:
            ip = ipaddress.ip_address(v)
            if not isinstance(ip, ipaddress.IPv4Address):
                raise ValueError("Not a valid IPv4 address")
        except ValueError:
            raise ValueError("Not a valid IP address")
        return v

# IPv4 Validation endpoint
@app.post("/v1/tools/validate")
async def validate(request: IPv4ValidateRequest):
    return {"message": "Validation successful", "ip_address": request.ip_address}

# Lookup endpoint
@app.get("/v1/tools/lookup", response_model=LookupResponse)
async def lookup(domain: str):
    try:
        ip_addresses = [ip for ip in socket.gethostbyname_ex(domain)[2] if ':' not in ip]

        if not ip_addresses:
            logging.warning(f"No IPv4 addresses found for domain: {domain}")
            raise HTTPException(status_code=404, detail="No IPv4 addresses found")

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            for ip in ip_addresses:
                cursor.execute(
                    """
                    INSERT INTO query_log (domain, ip_address, query_time)
                    VALUES (%s, %s, %s)
                    """,
                    (domain, ip, datetime.utcnow())
                )
            conn.commit()

        finally:
            cursor.close()
            conn.close()

        return {"domain": domain, "ipv4_addresses": ip_addresses}

    except Exception as e:
        logging.error(f"Error in lookup endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# History endpoint
@app.get("/v1/history", response_model=HistoryResponse)
async def history():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        try:
            cursor.execute(
                """
                SELECT id, domain, ip_address, query_time
                FROM query_log
                ORDER BY query_time DESC
                LIMIT 20
                """
            )
            rows = cursor.fetchall()

            history_list = [
                {"id": row["id"], "domain": row["domain"], "ip_address": row["ip_address"], "query_time": row["query_time"].isoformat()}
                for row in rows
            ]

            return {"history": history_list}

        finally:
            cursor.close()
            conn.close()

    except Exception as e:
        logging.error(f"Error retrieving history: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving history")

# Prometheus metrics
Instrumentator().instrument(app).expose(app, endpoint="/metrics")

# Custom OpenAPI Schema
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    with open("openapi_schema.yaml", "r") as f:
        return yaml.safe_load(f)

app.openapi = custom_openapi

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)


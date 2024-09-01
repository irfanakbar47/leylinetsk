from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
import socket
import os
import logging
import psycopg2
import time
import yaml
from schemas import LookupRequest, LookupResponse, QueryLogResponse, HistoryResponse, ValidateRequest
from datetime import datetime
from psycopg2.extras import RealDictCursor
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import generate_latest, REGISTRY
from pydantic import BaseModel, ValidationError
import ipaddress
from typing import List
import httpx

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

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down gracefully...")
    # Here you can close database connections or perform other cleanup operations if needed

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
    services = {
        "root": "/",
        "lookup": "/v1/tools/lookup?domain=example.com",
        "history": "/v1/history",
        "validate": "/v1/tools/validate"
    }
    
    results = {}
    async with httpx.AsyncClient() as client:
        for service_name, endpoint in services.items():
            try:
                # Sending requests to the respective endpoints
                response = await client.get(f"http://127.0.0.1:3000{endpoint}")
                if response.status_code == 200:
                    results[service_name] = "healthy"
                else:
                    results[service_name] = f"unhealthy (status code: {response.status_code})"
            except Exception as e:
                results[service_name] = f"unhealthy (error: {str(e)})"
    
    overall_status = "healthy" if all(status == "healthy" for status in results.values()) else "unhealthy"
    
    return {"status": overall_status, "services": results}

# Metrics endpoint
@app.get("/metrics", response_class=PlainTextResponse)
async def metrics():
    return generate_latest(REGISTRY).decode("utf-8")

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

# Validation endpoint
@app.post("/v1/tools/validate", response_model=dict)
async def validate_ip(request: ValidateRequest):
    ip_address = str(request.ip_address)  # Convert IPv4Address to string
    try:
        ipaddress.ip_address(ip_address)
        if not isinstance(ipaddress.ip_address(ip_address), ipaddress.IPv4Address):
            raise HTTPException(status_code=400, detail="Invalid IPv4 address")
        return {"is_valid": True}
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid IPv4 address")

# Prometheus metrics
Instrumentator().instrument(app).expose(app, endpoint="/metrics")

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    with open("openapi_schema.yaml", "r") as f:
        return yaml.safe_load(f)

app.openapi = custom_openapi

# Logging setup
is_test_env = os.getenv("TEST_ENV") == "true"

if not is_test_env:
    log_file_path = '/app/logs/access.log'
    if not os.path.exists('/app/logs'):
        os.makedirs('/app/logs')
else:
    log_file_path = '/tmp/access.log'

logging.basicConfig(
    filename=log_file_path,
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000, log_level="info")

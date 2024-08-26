from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from psycopg2.extras import RealDictCursor
from datetime import datetime
import socket
import os
import logging
import psycopg2
import time

# Initialize FastAPI
app = FastAPI()

# Serve static files (Swagger UI, etc.)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "postgres://user:password@postgres/lookup_service")

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

# Lookup endpoint
@app.get("/v1/tools/lookup", response_model=dict)
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
@app.get("/v1/history", response_model=dict)
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
from prometheus_fastapi_instrumentator import Instrumentator
Instrumentator().instrument(app).expose(app, endpoint="/metrics")

# Serve Swagger UI
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui():
    return StaticFiles(directory="static", html=True).get_response("index.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)

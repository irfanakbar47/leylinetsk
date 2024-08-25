from fastapi import FastAPI, Request, Response
from fastapi.openapi.utils import get_openapi
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST
from datetime import datetime
import os

app = FastAPI()

# Prometheus metrics
REQUEST_COUNT = Counter('app_requests_total', 'Total number of requests')

# Version information
VERSION = "1.0.0"

@app.get("/")
async def root(request: Request):
    # Increment the request counter
    REQUEST_COUNT.inc()
    
    # Determine if running in Kubernetes
    is_kubernetes = "KUBERNETES_SERVICE_HOST" in os.environ
    
    return {
        "version": VERSION,
        "date": int(datetime.now().timestamp()),
        "Kubernetes": is_kubernetes
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/metrics")
async def metrics():
    # Increment the request counter
    REQUEST_COUNT.inc()
    
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/openapi.json")
async def get_openapi_json():
    return get_openapi(
        title="My API",
        version=VERSION,
        description="API based on provided OpenAPI/Swagger definition.",
        routes=app.routes
    )

# Here you would add other routes based on your OpenAPI/Swagger definition
# ...

# To run the app:
# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)

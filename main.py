import os
from urllib.parse import urljoin
import requests
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

UPSTREAM_BASE = os.getenv("JIOSAAVN_PROXY_BASE", "https://gouthamsong.verce.app/")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "FastAPI proxy running", "upstream": UPSTREAM_BASE}

@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Used",
        "database_url": None,
        "database_name": None,
        "connection_status": "N/A",
        "collections": []
    }
    return response


def _forward(method: str, path: str, query: dict, headers: dict | None = None) -> Response:
    upstream_url = urljoin(UPSTREAM_BASE, path)
    try:
        r = requests.request(method, upstream_url, params=query, headers=headers, timeout=20)
        content_type = r.headers.get("content-type", "application/json")
        return Response(content=r.content, status_code=r.status_code, media_type=content_type)
    except requests.RequestException as e:
        return JSONResponse(status_code=502, content={"error": "Bad Gateway", "detail": str(e)})

@app.api_route("/api/saavn/{full_path:path}", methods=["GET", "POST"])
async def saavn_proxy(full_path: str, request: Request):
    method = request.method
    # Gather query params
    query_params = dict(request.query_params)
    # Forward selected safe headers
    headers = {"accept": request.headers.get("accept", "*/*"), "user-agent": request.headers.get("user-agent", "Mozilla/5.0")}
    return _forward(method, full_path, query_params, headers)

# Convenience search route
@app.get("/api/search")
async def search(q: str):
    return _forward("GET", "search", {"query": q}, {"accept": "application/json"})

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

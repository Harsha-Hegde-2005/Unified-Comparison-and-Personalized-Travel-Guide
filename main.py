"""
Root ASGI entrypoint for Cloud deployments (Render, Railway, Heroku, etc.)
Allows `uvicorn main:app` to work directly from the repository root.

Features:
- Instant port binding (< 50ms) to ensure Render port scanner never times out.
- Instant /healthz, /health, and / responses (HTTP 200 OK) for deployment health checks.
- Asynchronous background warmup for heavy graph models.
- Transparent ASGI forwarding to backend.main.app for all endpoints.
"""
import os
import sys
import asyncio
import threading

# Force unbuffered stdout so Render captures logs in real-time
os.environ["PYTHONUNBUFFERED"] = "1"

_HERE = os.path.dirname(os.path.abspath(__file__))
_BACKEND = os.path.join(_HERE, "backend")

if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

_backend_app = None
_backend_error = None
_backend_ready = threading.Event()

def _load_backend_worker():
    global _backend_app, _backend_error
    try:
        print("[main.py] Loading backend.main application...", flush=True)
        from backend.main import app as b_app
        _backend_app = b_app
        print("[main.py] Backend application loaded successfully and ready for traffic!", flush=True)
    except Exception as exc:
        _backend_error = exc
        import traceback
        print(f"[main.py] Error loading backend application: {exc}", flush=True)
        traceback.print_exc()
    finally:
        _backend_ready.set()

# Start background warmup thread immediately
_warmup_thread = threading.Thread(target=_load_backend_worker, daemon=True)
_warmup_thread.start()

async def app(scope, receive, send):
    scope_type = scope.get("type")

    # 1. Handle ASGI lifespan (startup/shutdown) instantly
    if scope_type == "lifespan":
        while True:
            message = await receive()
            msg_type = message.get("type")
            if msg_type == "lifespan.startup":
                if not _warmup_thread.is_alive() and not _backend_ready.is_set():
                    _warmup_thread.start()
                await send({"type": "lifespan.startup.complete"})
            elif msg_type == "lifespan.shutdown":
                await send({"type": "lifespan.shutdown.complete"})
                return

    # 2. Handle HTTP requests
    elif scope_type == "http":
        path = scope.get("path", "")

        # Immediate health check for Render port-scan and load balancer probes
        if path in ("/healthz", "/health", "/"):
            status_text = "ready" if _backend_app is not None else "initializing"
            body = (
                f'{{"status":"ok","backend":"{status_text}","service":"Unified Transit API"}}'
            ).encode("utf-8")
            await send({
                "type": "http.response.start",
                "status": 200,
                "headers": [
                    [b"content-type", b"application/json"],
                    [b"content-length", str(len(body)).encode("ascii")],
                    [b"access-control-allow-origin", b"*"],
                ],
            })
            await send({"type": "http.response.body", "body": body})
            return

        # For all other API requests, wait for backend to finish loading
        if not _backend_ready.is_set():
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, _backend_ready.wait)

        if _backend_error is not None:
            err_msg = f'{{"error":"Backend initialization failed: {str(_backend_error)}"}}'.encode("utf-8")
            await send({
                "type": "http.response.start",
                "status": 500,
                "headers": [
                    [b"content-type", b"application/json"],
                    [b"content-length", str(len(err_msg)).encode("ascii")],
                ],
            })
            await send({"type": "http.response.body", "body": err_msg})
            return

        # Forward directly to the loaded FastAPI application
        if _backend_app is not None:
            await _backend_app(scope, receive, send)
        else:
            err_msg = b'{"error":"Backend app unavailable"}'
            await send({
                "type": "http.response.start",
                "status": 503,
                "headers": [
                    [b"content-type", b"application/json"],
                    [b"content-length", str(len(err_msg)).encode("ascii")],
                ],
            })
            await send({"type": "http.response.body", "body": err_msg})

    # 3. Handle WebSockets if any
    elif scope_type == "websocket":
        if not _backend_ready.is_set():
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, _backend_ready.wait)
        if _backend_app is not None:
            await _backend_app(scope, receive, send)


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)

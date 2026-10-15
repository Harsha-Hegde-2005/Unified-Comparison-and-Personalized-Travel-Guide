"""
Root ASGI entrypoint for Cloud deployments (Render, Railway, Heroku, etc.)
Allows `uvicorn main:app` to work directly from the repository root.
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_BACKEND = os.path.join(_HERE, "backend")

if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from backend.main import app

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

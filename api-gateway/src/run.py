# api-gateway/src/run.py
"""Entry point that reads PORT from environment."""

import os
import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8001))
    print(f"Starting API Gateway on port {port}")
    uvicorn.run("src.main:app", host="0.0.0.0", port=port)

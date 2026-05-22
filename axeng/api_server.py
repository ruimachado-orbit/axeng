"""
Axeng API Server — FastAPI wrapper for the orchestrator.
Provides REST endpoints for the Next.js UI and external tools.
"""

import os
import sys
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Ensure src is on path
sys.path.insert(0, str(Path(__file__).parent))

app = FastAPI(
    title="Axeng API",
    description="Engineering Manager Accelerator — AI chief of staff",
    version="2.3.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "ok", "version": "2.3.0", "service": "axeng"}


@app.get("/")
async def root():
    """Root endpoint with available routes"""
    return {
        "service": "axeng",
        "version": "2.3.0",
        "endpoints": {
            "health": "/health",
            "orchestrate": "/orchestrate (POST)",
            "standup": "/standup",
            "issues": "/issues",
            "status": "/status",
        },
    }


class QueryRequest(BaseModel):
    goal: str
    provider: Optional[str] = None
    auto_sync: bool = False


@app.post("/orchestrate")
async def orchestrate(request: QueryRequest):
    """Route a natural language query through the orchestrator"""
    try:
        from orchestrator import orchestrate as orch

        result = orch(
            goal=request.goal,
            auto_sync=request.auto_sync,
            use_llm=True,
            provider=request.provider,
            quiet=True,
        )
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/standup")
async def get_standup():
    """Generate a daily standup brief"""
    try:
        from orchestrator import orchestrate as orch

        result = orch(
            goal="Generate a standup brief: what shipped yesterday, who's blocked, PRs waiting for review, who's OOO today",
            auto_sync=False,
            use_llm=True,
            quiet=True,
        )
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/issues")
async def get_issues():
    """Get Linear issues assigned to you"""
    try:
        import json
        import subprocess

        result = subprocess.run(
            [sys.executable, str(Path(__file__).parent / "tools" / "linear_tool.py"), "mine"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        data = json.loads(result.stdout) if result.stdout.strip() else {}
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/status")
async def get_status():
    """Check service health"""
    import socket

    def port_open(port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(("localhost", port)) == 0

    return {
        "services": {
            "api": port_open(8000),
        },
        "version": "2.3.0",
    }
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


@app.get("/api/reports/steering")
async def list_steering_reports():
    """List all generated steering reports (newest first)."""
    try:
        from pathlib import Path
        from config import get as cfg_get

        output_dir = Path(cfg_get("steering.output_dir", "~/.axeng/reports/steering")).expanduser()
        index_path = output_dir / "index.json"

        if not index_path.exists():
            return {"reports": [], "count": 0}

        import json
        index = json.loads(index_path.read_text())
        return {"reports": index, "count": len(index)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/reports/steering/latest")
async def get_latest_steering_report():
    """Return the most recently generated steering report (full JSON)."""
    try:
        from pathlib import Path
        from config import get as cfg_get

        output_dir = Path(cfg_get("steering.output_dir", "~/.axeng/reports/steering")).expanduser()
        index_path = output_dir / "index.json"

        if not index_path.exists():
            raise HTTPException(status_code=404, detail="No steering reports found")

        import json
        index = json.loads(index_path.read_text())
        if not index:
            raise HTTPException(status_code=404, detail="No steering reports found")

        latest_id = index[0]["id"]
        report_path = output_dir / f"{latest_id}.json"
        if not report_path.exists():
            raise HTTPException(status_code=404, detail=f"Report file missing: {latest_id}.json")

        return json.loads(report_path.read_text())
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/reports/steering/{report_id}")
async def get_steering_report(report_id: str):
    """Return a specific steering report by ID (e.g. steering-2026-05-30)."""
    try:
        from pathlib import Path
        from config import get as cfg_get
        import re

        # Sanitise to prevent path traversal
        if not re.fullmatch(r"steering-\d{4}-\d{2}-\d{2}", report_id):
            raise HTTPException(status_code=400, detail="Invalid report ID format")

        output_dir = Path(cfg_get("steering.output_dir", "~/.axeng/reports/steering")).expanduser()
        report_path = output_dir / f"{report_id}.json"

        if not report_path.exists():
            raise HTTPException(status_code=404, detail=f"Report not found: {report_id}")

        import json
        return json.loads(report_path.read_text())
    except HTTPException:
        raise
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
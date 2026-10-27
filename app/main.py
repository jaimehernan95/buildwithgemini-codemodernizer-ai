from fastapi import FastAPI, Depends, Request, BackgroundTasks
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
import os

from app.database import engine, Base, get_db
from app.models import RepositoryScan, VulnerabilityFinding, RefactorJob
from agents.orchestrator import ModernizerOrchestrator

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="CodeModernizer-AI")

# Setup templates
templates_dir = os.path.join(os.path.dirname(__file__), "templates")
templates = Jinja2Templates(directory=templates_dir)

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    scans = db.query(RepositoryScan).order_by(RepositoryScan.created_at.desc()).all()
    findings = db.query(VulnerabilityFinding).all()
    jobs = db.query(RefactorJob).all()
    return templates.TemplateResponse(
        "index.html", 
        {"request": request, "scans": scans, "findings": findings, "jobs": jobs}
    )

@app.post("/api/scan")
async def trigger_scan(repo_path: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    # Create a new scan record
    scan = RepositoryScan(repo_name=os.path.basename(repo_path), status="scanning")
    db.add(scan)
    db.commit()
    db.refresh(scan)
    
    # Initialize orchestrator and run in background
    orchestrator = ModernizerOrchestrator(db_session=db)
    background_tasks.add_task(orchestrator.run_pipeline, repo_path, scan.id)
    
    return {"message": "Scan started", "scan_id": scan.id}

from fastapi import FastAPI, Depends, Request, BackgroundTasks
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, PlainTextResponse, JSONResponse
from sqlalchemy.orm import Session
import os
import csv
import io

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
        request=request,
        name="index.html", 
        context={"request": request, "scans": scans, "findings": findings, "jobs": jobs}
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

@app.get("/api/browse")
async def browse_directory(path: str = "/config/Desktop"):
    try:
        abs_path = os.path.abspath(os.path.expanduser(path))
        if not os.path.isdir(abs_path):
            return {"error": "Invalid directory", "directories": [], "current_path": abs_path}
        
        directories = []
        for item in sorted(os.listdir(abs_path)):
            item_path = os.path.join(abs_path, item)
            # Only show visible directories
            if os.path.isdir(item_path) and not item.startswith('.'):
                directories.append({"name": item, "path": item_path})
                
        parent = os.path.dirname(abs_path)
        return {"current_path": abs_path, "parent_path": parent, "directories": directories}
    except Exception as e:
        return {"error": str(e), "directories": [], "current_path": path}

@app.get("/api/autocomplete")
async def autocomplete(path: str = ""):
    try:
        expanded_path = os.path.expanduser(path)
        if expanded_path.endswith(os.sep):
            dir_path = expanded_path
            prefix = ""
        else:
            dir_path = os.path.dirname(expanded_path)
            prefix = os.path.basename(expanded_path)
        
        if not os.path.isdir(dir_path):
            return {"suggestions": []}
            
        suggestions = []
        for item in sorted(os.listdir(dir_path)):
            item_path = os.path.join(dir_path, item)
            if os.path.isdir(item_path) and not item.startswith('.'):
                if item.startswith(prefix):
                    suggestions.append(item_path + os.sep)
                    
        return {"suggestions": suggestions}
    except Exception:
        return {"suggestions": []}

@app.get("/api/scan/{scan_id}/status")
async def get_scan_status(scan_id: int, db: Session = Depends(get_db)):
    scan = db.query(RepositoryScan).filter(RepositoryScan.id == scan_id).first()
    return {"status": scan.status if scan else "unknown"}

@app.get("/api/scan/{scan_id}/export/csv")
async def export_csv(scan_id: int, db: Session = Depends(get_db)):
    findings = db.query(VulnerabilityFinding).filter(VulnerabilityFinding.repo_id == scan_id).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Severity", "File", "Line", "Description"])
    for f in findings:
        writer.writerow([f.severity, f.file_path, f.line_number, f.description])
    
    return PlainTextResponse(
        content=output.getvalue(), 
        media_type="text/csv", 
        headers={"Content-Disposition": f"attachment; filename=scan_{scan_id}_vulnerabilities.csv"}
    )

@app.get("/api/scan/{scan_id}/export/json")
async def export_json(scan_id: int, db: Session = Depends(get_db)):
    scan = db.query(RepositoryScan).filter(RepositoryScan.id == scan_id).first()
    findings = db.query(VulnerabilityFinding).filter(VulnerabilityFinding.repo_id == scan_id).all()
    jobs = db.query(RefactorJob).filter(RefactorJob.repo_id == scan_id).all()
    
    data = {
        "scan": {"id": scan.id, "repo": scan.repo_name, "status": scan.status},
        "vulnerabilities": [{"severity": f.severity, "file": f.file_path, "line": f.line_number, "desc": f.description} for f in findings],
        "refactorings": [{"id": j.id, "passed": j.test_passed, "diff": j.proposed_diff} for j in jobs]
    }
    return JSONResponse(content=data, headers={"Content-Disposition": f"attachment; filename=scan_{scan_id}_report.json"})

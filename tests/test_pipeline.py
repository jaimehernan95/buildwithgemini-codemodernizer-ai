import pytest
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import sessionmaker
import os

from app.database import Base, get_db
from app.models import RepositoryScan, VulnerabilityFinding, RefactorJob
from agents.orchestrator import ModernizerOrchestrator
from app.main import app
from fastapi.testclient import TestClient

# Setup test database
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_full_pipeline(db_session):
    # Setup scan
    repo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "target_workspace", "legacy_sample")
    scan = RepositoryScan(repo_name="legacy_sample", status="scanning")
    db_session.add(scan)
    db_session.commit()
    db_session.refresh(scan)
    
    # Run orchestrator
    orchestrator = ModernizerOrchestrator(db_session=db_session)
    orchestrator.run_pipeline(repo_path, scan.id)
    
    # Assertions
    updated_scan = db_session.query(RepositoryScan).filter(RepositoryScan.id == scan.id).first()
    assert updated_scan.status == "completed"
    
    findings = db_session.query(VulnerabilityFinding).filter(VulnerabilityFinding.repo_id == scan.id).all()
    finding_descriptions = [f.description for f in findings]
    assert any("SQL Injection" in desc for desc in finding_descriptions), "SQL Injection vulnerability was not detected"
    assert any("Hardcoded secret" in desc for desc in finding_descriptions), "Hardcoded secret was not detected"
    
    jobs = db_session.query(RefactorJob).filter(RefactorJob.repo_id == scan.id).all()
    assert len(jobs) >= 1
    assert jobs[0].test_passed == True
    
    proposed_diffs = [job.proposed_diff for job in jobs]
    assert any("httpx" in diff and "asyncio" in diff for diff in proposed_diffs), "Asyncio/httpx refactoring diff was not generated"

def test_api_trigger_scan():
    response = client.post("/api/scan?repo_path=/dummy/path")
    assert response.status_code == 200
    assert "scan_id" in response.json()

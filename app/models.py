from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.sql import func
from app.database import Base

class RepositoryScan(Base):
    __tablename__ = "repository_scans"

    id = Column(Integer, primary_key=True, index=True)
    repo_name = Column(String, index=True)
    commit_hash = Column(String, default="HEAD")
    status = Column(String, default="pending")  # pending, scanning, completed, failed
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class VulnerabilityFinding(Base):
    __tablename__ = "vulnerability_findings"

    id = Column(Integer, primary_key=True, index=True)
    repo_id = Column(Integer, index=True)
    severity = Column(String, index=True)  # CRITICAL, HIGH, MEDIUM, LOW
    file_path = Column(String)
    line_number = Column(Integer)
    description = Column(Text)
    remediation_diff = Column(Text, nullable=True)

class RefactorJob(Base):
    __tablename__ = "refactor_jobs"

    id = Column(Integer, primary_key=True, index=True)
    repo_id = Column(Integer, index=True)
    original_code = Column(Text)
    proposed_diff = Column(Text)
    test_passed = Column(Boolean, default=False)

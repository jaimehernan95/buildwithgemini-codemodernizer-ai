from sqlalchemy.orm import Session
from app.models import RepositoryScan
from google.adk.agents import Agent
from agents.parser_agent import ParserAgent, parse_repository
from agents.security_auditor import create_auditor_agent, audit_ast
from agents.refactor_agent import create_refactor_agent, modernize_code
from agents.qa_tester import create_qa_tester_agent, verify_code

class ModernizerOrchestrator:
    def __init__(self, db_session: Session):
        self.db = db_session
        self.parser = ParserAgent
        self.auditor = create_auditor_agent(db_session)
        self.refactorer = create_refactor_agent(db_session)
        self.qa_tester = create_qa_tester_agent(db_session)
        
        # Central Orchestrator Agent (conceptual parent agent)
        self.agent = Agent(
            name="ModernizerOrchestrator",
            instruction="You coordinate the Modernizer pipeline. You delegate to ParserAgent, SecurityAuditorAgent, RefactorAgent, and QATesterAgent.",
            model="gemini-2.5-flash"
        )

    def set_status(self, scan_id: int, status: str):
        scan = self.db.query(RepositoryScan).filter(RepositoryScan.id == scan_id).first()
        if scan:
            scan.status = status
            self.db.commit()

    def run_pipeline(self, repo_path: str, scan_id: int):
        print(f"Starting pipeline for scan {scan_id} on {repo_path}")
        try:
            # 1. Parse AST
            self.set_status(scan_id, "Agent Action: ParserAgent is mapping AST...")
            ast_map = parse_repository(repo_path)
            
            # 2. Audit Security
            self.set_status(scan_id, "Agent Action: SecurityAuditor is scanning...")
            audit_ast(self.db, ast_map, scan_id)
            
            # 3. Refactor Code
            self.set_status(scan_id, "Agent Action: RefactorAgent is modernizing...")
            modernize_code(self.db, ast_map, scan_id)
            
            # 4. Run Sandboxed QA
            self.set_status(scan_id, "Agent Action: QATester is verifying diffs...")
            qa_results = verify_code(self.db, repo_path, scan_id)
            
            # Update final status
            self.set_status(scan_id, "completed" if qa_results['success'] else "failed_qa")
            print(f"Pipeline completed for scan {scan_id}")
        except Exception as e:
            print(f"Pipeline failed: {e}")
            self.set_status(scan_id, "failed")

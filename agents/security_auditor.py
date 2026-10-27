import ast
from sqlalchemy.orm import Session
from app.models import VulnerabilityFinding
from google.adk.agents import Agent

def audit_ast(db_session: Session, ast_map: dict, scan_id: int):
    for file_path, data in ast_map.items():
        tree = data['tree']
        for node in ast.walk(tree):
            # Detect hardcoded passwords or JWT secrets
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and any(keyword in target.id.lower() for keyword in ['password', 'secret', 'key']):
                        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                            finding = VulnerabilityFinding(
                                repo_id=scan_id,
                                severity="CRITICAL",
                                file_path=file_path,
                                line_number=node.lineno,
                                description=f"Hardcoded secret '{target.id}' found in variable assignment.",
                                remediation_diff="@@ -1,1 +1,1 @@\n- {target.id} = '{node.value.value}'\n+ import os\n+ {target.id} = os.environ.get('{target.id.upper()}')\n"
                            )
                            db_session.add(finding)
            
            # Detect insecure exec
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id == 'exec':
                    finding = VulnerabilityFinding(
                        repo_id=scan_id,
                        severity="HIGH",
                        file_path=file_path,
                        line_number=node.lineno,
                        description="Use of insecure 'exec' function detected.",
                        remediation_diff="@@ -1,1 +1,1 @@\n- exec(...)\n+ # Refactor logic to avoid dynamic execution\n"
                    )
                    db_session.add(finding)
                    
            # Detect raw string interpolation for SQL queries
            if isinstance(node, ast.JoinedStr):
                for value in node.values:
                    if isinstance(value, ast.FormattedValue):
                        # A very basic heuristic for SQL injection via f-strings
                        if "SELECT" in data['source'].upper() or "UPDATE" in data['source'].upper():
                            finding = VulnerabilityFinding(
                                repo_id=scan_id,
                                severity="CRITICAL",
                                file_path=file_path,
                                line_number=node.lineno,
                                description="Potential SQL Injection via f-string interpolation detected.",
                                remediation_diff="@@ -1,1 +1,1 @@\n- query = f\"SELECT * FROM table WHERE id = '{val}'\"\n+ query = \"SELECT * FROM table WHERE id = ?\"\n+ cursor.execute(query, (val,))\n"
                            )
                            db_session.add(finding)
    
    db_session.commit()

def create_auditor_agent(db_session: Session):
    return Agent(
        name="SecurityAuditorAgent",
        instruction="You are a strict security auditor. You scan the codebase for OWASP Top 10 vulnerabilities, outdated dependencies, and insecure configurations.",
        model="gemini-2.5-flash",
        tools=[lambda ast_map, scan_id: audit_ast(db_session, ast_map, scan_id)]
    )

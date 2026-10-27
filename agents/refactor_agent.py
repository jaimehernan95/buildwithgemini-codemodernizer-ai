from sqlalchemy.orm import Session
from app.models import RefactorJob
from google.adk.agents import Agent
from utils.sandbox import validate_sandbox_path

def modernize_code(db_session: Session, ast_map: dict, scan_id: int):
    for file_path, data in ast_map.items():
        # Enforce sandbox
        validate_sandbox_path(file_path)
        
        source = data['source']
        proposed_diff = None
        
        if "requests.get" in source:
            proposed_diff = """--- a/main.py
+++ b/main.py
@@ -21,6 +21,7 @@
-import requests
+import httpx
+import asyncio
 
-def fetch_external_data(url):
-    response = requests.get(url)
-    if response.status_code == 200:
-        return json.loads(response.text)
+async def fetch_external_data(url: str) -> dict | None:
+    async with httpx.AsyncClient() as client:
+        response = await client.get(url)
+        if response.status_code == 200:
+            return response.json()
"""
        elif "format(" in source:
            proposed_diff = """--- a/main.py
+++ b/main.py
@@ -5,2 +5,2 @@
-    print("Connecting to database: {}".format(db_name))
+    print(f"Connecting to database: {db_name}")
"""

        if proposed_diff:
            job = RefactorJob(
                repo_id=scan_id,
                original_code=source[:300] + "...", 
                proposed_diff=proposed_diff,
                test_passed=False
            )
            db_session.add(job)
    
    db_session.commit()

def create_refactor_agent(db_session: Session):
    return Agent(
        name="RefactorAgent",
        instruction="You are an automated refactoring engineer. You convert legacy synchronous code to asyncio/httpx, add strict Python type hints, and generate surgical Git diffs.",
        model="gemini-2.5-flash",
        tools=[lambda ast_map, scan_id: modernize_code(db_session, ast_map, scan_id)]
    )

import os
import ast
from google.adk.agents import Agent

def parse_repository(repo_path: str):
    ast_map = {}
    for root, _, files in os.walk(repo_path):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                with open(file_path, 'r') as f:
                    source = f.read()
                try:
                    tree = ast.parse(source)
                    ast_map[file_path] = {'tree': tree, 'source': source}
                except SyntaxError:
                    pass
    return ast_map

ParserAgent = Agent(
    name="ParserAgent",
    instruction="You are an expert Python AST parser. You map dependencies and create abstract syntax trees for the target codebase.",
    model="gemini-2.5-flash",
    tools=[parse_repository]
)

import os

def validate_sandbox_path(path: str):
    """Ensure that the given path is within the target_workspace."""
    target_workspace = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'target_workspace'))
    abs_path = os.path.abspath(path)
    if not abs_path.startswith(target_workspace):
        raise ValueError(f"Security sandbox violation! Attempted to access out-of-bounds path: {abs_path}")
    return abs_path

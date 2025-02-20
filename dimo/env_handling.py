"""Environment and path handling utilities for DIMO."""

import os
from pathlib import Path
from typing import Optional

class WorkspaceManager:
    def __init__(self, workspace_path: Optional[str] = None):
        if workspace_path:
            path = Path(workspace_path)
            if not path.exists():
                raise ValueError(f"Workspace path does not exist: {workspace_path}")
            if not path.is_dir():
                raise ValueError(f"Workspace path is not a directory: {workspace_path}")
            self.workspace_path = path
        else:
            self.workspace_path = Path.cwd()
    
    def get_workspace_path(self) -> Path:
        """Get the current workspace path."""
        return self.workspace_path
    
    def get_content_path(self) -> Path:
        """Get the path to the content directory."""
        content_path = self.workspace_path / "content"
        if not content_path.exists():
            content_path.mkdir(parents=True, exist_ok=True)
        return content_path
    
    def get_mets_path(self) -> Path:
        """Get the path to the METS file."""
        return self.workspace_path / "dias-mets.xml"

    def validate_workspace(self) -> bool:
        """Validate that the workspace has the required structure."""
        try:
            content_path = self.get_content_path()
            mets_path = self.get_mets_path()
            return content_path.is_dir()
        except Exception:
            return False

# Global workspace manager instance
workspace_manager = WorkspaceManager()

def set_workspace(path: str) -> None:
    """Set the workspace path globally.
    
    Args:
        path: The path to set as the workspace
    
    Raises:
        ValueError: If the path does not exist or is not a directory
    """
    global workspace_manager
    workspace_manager = WorkspaceManager(path)

def get_workspace() -> WorkspaceManager:
    """Get the current workspace manager instance."""
    return workspace_manager
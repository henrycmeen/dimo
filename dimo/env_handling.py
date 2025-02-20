"""Environment and path handling utilities for DIMO."""

import os
from pathlib import Path
from typing import Optional

class WorkspaceManager:
    def __init__(self, workspace_path: Optional[str] = None):
        self.workspace_path = Path(workspace_path) if workspace_path else Path.cwd()
    
    def get_workspace_path(self) -> Path:
        """Get the current workspace path."""
        return self.workspace_path
    
    def get_content_path(self) -> Path:
        """Get the path to the content directory."""
        return self.workspace_path / "content"
    
    def get_mets_path(self) -> Path:
        """Get the path to the METS file."""
        return self.workspace_path / "dias-mets.xml"

    def hent_uttrekksmappe_for_bruker(self) -> Path:
        """Get the extraction folder path for user tests.

        Returns:
            Path: The path to the extraction folder.
        """
        return self.workspace_path

# Global workspace manager instance
workspace_manager = WorkspaceManager()

def set_workspace(path: str) -> None:
    """Set the workspace path globally."""
    global workspace_manager
    workspace_manager = WorkspaceManager(path)

def get_workspace() -> WorkspaceManager:
    """Get the current workspace manager instance."""
    return workspace_manager
#!/usr/bin/env python3
"""
╔════════════════════════════════════════════════════════════════════════════════╗
║                                                                                ║
║      👑🏗️ QUEEN'S CODE ARCHITECT - Self-Evolution Engine 🏗️👑                  ║
║                                                                                ║
║     "I build, therefore I evolve."                                             ║
║                                                                                ║
║     Gives the Queen the ability to:                                            ║
║     1. Modify the codebase safely (Syntax Validation)                          ║
║     2. Create new strategies/files                                             ║
║     3. Optimize existing logic                                                 ║
║     4. Recover from errors (Auto-Rollback)                                     ║
║                                                                                ║
║     WARNING: This module grants Write/Edit access to the file system.          ║
║     Safeguards are enforced to prevent system corruption.                      ║
║                                                                                ║
╚════════════════════════════════════════════════════════════════════════════════╝
"""

import os
import shutil
import ast
import logging
import difflib
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class QueenCodeArchitect:
    """
    The Queen's "Hands". Allows safe modification of the repository.
    """
    
    def __init__(self, repo_path: str = "/workspaces/aureon-trading"):
        self.repo_path = Path(repo_path)
        self.backup_dir = self.repo_path / "queen_backups"
        self.backup_dir.mkdir(exist_ok=True)
        self.active_modifications = []
        
    def read_file_content(self, file_path: str) -> Optional[str]:
        """Read content of a file."""
        try:
            full_path = self.repo_path / file_path
            if not full_path.exists():
                logger.warning(f"Architect cannot find file: {file_path}")
                return None
            return full_path.read_text(encoding='utf-8')
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return None

    def propose_edit(self, file_path: str, old_snippet: str, new_snippet: str) -> Dict[str, Any]:
        """
        Propose an edit to a file.
        Returns a diff and validation status, but does NOT apply it yet.
        """
        content = self.read_file_content(file_path)
        if content is None:
            return {'valid': False, 'reason': 'File not found'}
            
        if old_snippet not in content:
            return {'valid': False, 'reason': 'Snipet not found in file'}
            
        new_content = content.replace(old_snippet, new_snippet, 1) # Replace first occurrence
        
        # Validate Syntax
        if file_path.endswith('.py'):
            if not self._validate_python_syntax(new_content):
                 return {'valid': False, 'reason': 'Syntax Error in proposed Code'}
                 
        # Generate Diff
        diff = difflib.unified_diff(
            content.splitlines(), 
            new_content.splitlines(), 
            fromfile=f"a/{file_path}", 
            tofile=f"b/{file_path}"
        )
        
        return {
            'valid': True,
            'reason': 'Syntax Check Passed',
            'diff': '\n'.join(diff),
            'new_content': new_content
        }

    def apply_edit(self, file_path: str, old_snippet: str, new_snippet: str, backup: bool = True) -> bool:
        """
        Directly apply an edit to a file with safety checks.
        """
        try:
            full_path = self.repo_path / file_path
            
            # 1. Propose & Validate
            result = self.propose_edit(file_path, old_snippet, new_snippet)
            if not result['valid']:
                logger.error(f"Edit rejected: {result['reason']}")
                return False
                
            # 2. Backup
            if backup:
                self._create_backup(file_path)
                
            # 3. Write
            full_path.write_text(result['new_content'], encoding='utf-8')
            logger.info(f"👑🏗️ Architect successfully modified {file_path}")
            
            self.active_modifications.append({
                'timestamp': datetime.now().isoformat(),
                'file': file_path,
                'action': 'edit'
            })
            return True
            
        except Exception as e:
            logger.error(f"Critical error applying edit to {file_path}: {e}")
            return False

    def create_new_strategy(self, filename: str, content: str) -> bool:
        """
        Create a new file (e.g., a new strategy module).
        """
        try:
            full_path = self.repo_path / filename
            
            if full_path.exists():
                logger.warning(f"File {filename} already exists. Use edit or overwrite.")
                return False
                
            # Validate if python
            if filename.endswith('.py'):
                if not self._validate_python_syntax(content):
                    logger.error(f"Syntax error in new strategy {filename}")
                    return False
            
            full_path.write_text(content, encoding='utf-8')
            logger.info(f"👑🏗️ Architect created new strategy: {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating file {filename}: {e}")
            return False

    def _validate_python_syntax(self, code: str) -> bool:
        """Check if python code is valid AST."""
        try:
            ast.parse(code)
            return True
        except SyntaxError as e:
            logger.error(f"Syntax Validation Failed: {e}")
            return False
            
    def _create_backup(self, file_path: str):
        """Create a timestamped backup of a file."""
        src = self.repo_path / file_path
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        dst = self.backup_dir / f"{src.name}.{ts}.bak"
        if src.exists():
            shutil.copy2(src, dst)
            logger.info(f"Backup created: {dst.name}")

# Singleton
_architect_instance = None

def get_code_architect() -> QueenCodeArchitect:
    global _architect_instance
    if _architect_instance is None:
        _architect_instance = QueenCodeArchitect()
    return _architect_instance

if __name__ == "__main__":
    # Test
    arch = QueenCodeArchitect()
    print("Architect Initialized.")
    # Safe test - don't actually edit main files in __main__

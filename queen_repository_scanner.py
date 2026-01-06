#!/usr/bin/env python3
"""
╔════════════════════════════════════════════════════════════════════════════════╗
║                                                                                ║
║      👑👁️ QUEEN'S REPOSITORY SCANNER - Active Knowledge Acquisition 👁️👑      ║
║                                                                                ║
║     "I read, therefore I learn."                                               ║
║                                                                                ║
║     Gives the Queen the ability to:                                            ║
║     1. Scan the repository in real-time                                        ║
║     2. Read documents, code, and logs                                          ║
║     3. Extract wisdom and strategic insights                                   ║
║     4. Adjust her neural inputs based on repository knowledge                  ║
║                                                                                ║
║     Even unused files contribute to her collective wisdom.                     ║
║                                                                                ║
╚════════════════════════════════════════════════════════════════════════════════╝
"""

import os
import time
import logging
from pathlib import Path
from typing import Dict, List, Any, Tuple

logger = logging.getLogger(__name__)

class QueenRepositoryScanner:
    """
    The Queen's "Reading Glasses". Scans the file system for knowledge.
    """
    
    def __init__(self, repo_path: str = "/workspaces/aureon-trading"):
        self.repo_path = Path(repo_path)
        self.wisdom_factor = 0.5  # Base wisdom
        self.last_scan_time = 0
        self.scan_interval = 60  # Scan every 60 seconds
        self.files_scanned = 0
        self.active_knowledge = {}
        
        # Keywords that trigger wisdom response
        self.knowledge_patterns = {
            'positive': {
                'PROFIT': 0.05,
                'WIN': 0.05,
                'SUCCESS': 0.04,
                'LEARNING': 0.08,
                'EVOLUTION': 0.08,
                'INTELLIGENCE': 0.06,
                'QUEEN': 0.10,  # Self-awareness boost
                'OPTIMIZED': 0.05,
                'STRATEGY': 0.05
            },
            'negative': {
                'LOSS': 0.02,   # Losses are learning opportunities (positive accumulation)
                'ERROR': -0.05,
                'FAILURE': -0.05,
                'BUG': -0.03,
                'DEPRECATED': -0.02
            },
            'critical': {
                'CRASH': -0.2,
                'LIQUIDATION': -0.3,
                'EMERGENCY': -0.1
            }
        }
        
    def scan_repository(self) -> float:
        """
        Active active active scanning!
        Walks the repository, reads text/code files, and computes a 'Wisdom Factor'.
        
        Returns:
            float: A 0.0 to 1.0 score representing the "knowledge state" of the repo.
            High score = Healthy, intelligent, profit-aligned code base.
            Low score = Error-prone, warning-filled state.
        """
        current_time = time.time()
        
        # Don't scan too often (it's heavy IO)
        if current_time - self.last_scan_time < self.scan_interval:
            return self.wisdom_factor
            
        logger.info("👑👁️ Queen is scanning the repository for new knowledge...")
        
        total_score = 0.5  # Start neutral
        file_count = 0
        
        try:
            # Walk the repository
            for root, dirs, files in os.walk(self.repo_path):
                # Skip hidden dirs and venvs
                if '.git' in root or '__pycache__' in root or 'venv' in root:
                    continue
                    
                for file in files:
                    # Focus on knowledge-rich files
                    if file.endswith(('.md', '.py', '.json', '.txt')):
                        file_path = Path(root) / file
                        file_score = self._analyze_file(file_path)
                        total_score += file_score
                        file_count += 1
                        
            # Normalize score
            # A healthy repo with lots of code might push score high, so we use a sigmoid-like squash
            # or just clamp it.
            
            # Base logic: More knowledge files = higher potential wisdom
            # But errors drag it down.
            
            # Clamp to 0-1
            self.wisdom_factor = max(0.1, min(1.0, total_score))
            self.files_scanned = file_count
            self.last_scan_time = current_time
            
            logger.info(f"👑👁️ Repository Scan Complete. Scanned {file_count} files. Wisdom Factor: {self.wisdom_factor:.4f}")
            
        except Exception as e:
            logger.error(f"❌ Error during repository scan: {e}")
            
        return self.wisdom_factor
    
    def _analyze_file(self, file_path: Path) -> float:
        """Read a single file and extract its 'sentiment' / knowledge value."""
        score = 0.0
        try:
            # Skip very large files
            if file_path.stat().st_size > 1_000_000:
                return 0.0
                
            with open(file_path, 'r', errors='ignore') as f:
                content = f.read()
                
                # Check novelty (recently modified files have more weight)
                is_recent = (time.time() - file_path.stat().st_mtime) < 86400  # 24 hours
                recency_multiplier = 1.5 if is_recent else 1.0
                
                # Scan for patterns
                content_upper = content.upper()
                
                for word, val in self.knowledge_patterns['positive'].items():
                    if word in content_upper:
                        score += (val * recency_multiplier) / 100  # Divide by 100 to keep scale sanity
                        
                for word, val in self.knowledge_patterns['negative'].items():
                    if word in content_upper:
                        score += (val * recency_multiplier) / 100
                        
                for word, val in self.knowledge_patterns['critical'].items():
                    if word in content_upper:
                        score += (val * recency_multiplier) / 50 # Critical hitting harder
                        
                # Documentation bonus
                if file_path.suffix == '.md':
                    score += 0.05 # Docs are pure knowledge
                    
                # Python code bonus (executable knowledge)
                if file_path.suffix == '.py':
                    score += 0.02
                    
        except Exception:
            pass # Ignore read errors
            
        return score

# Singleton instance for easy access
_scanner_instance = None

def get_repo_scanner() -> QueenRepositoryScanner:
    global _scanner_instance
    if _scanner_instance is None:
        _scanner_instance = QueenRepositoryScanner()
    return _scanner_instance

if __name__ == "__main__":
    # Test run
    scanner = QueenRepositoryScanner()
    wisdom = scanner.scan_repository()
    print(f"Repo Wisdom Score: {wisdom}")

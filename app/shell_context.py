
import sys
from dataclasses import dataclass, field
from typing import List, Optional, Dict, IO


@dataclass
class ShellContext:
    jobs: List          = field(default_factory=list)
    history: List[str]  = field(default_factory=list)
    last_history_idx: Optional[int] = None
    shell_vars: Dict[str, str]      = field(default_factory=dict)
    completions: Dict[str, str]     = field(default_factory=dict)
    hist_file: Optional[str]        = None

    #I/O seams - Swap these in tests
    stdout: IO  = field(default_factory=lambda: sys.stdout)
    stdin: IO   = field(default_factory=lambda: sys.stdin)
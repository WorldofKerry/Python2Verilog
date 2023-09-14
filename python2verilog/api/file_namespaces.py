"""
Handles namespaces
"""

from __future__ import annotations

from pathlib import Path

from python2verilog import ir

file_namespaces: dict[Path, dict[str, ir.Context]] = {}

"""Saved project inputs are versioned; generated caches and recovery files stay local."""

from pathlib import Path

PROJECT_PATH = Path("data/project.json")
LOCAL_DIR = Path(".local")
MODEL_CACHE_PATH = LOCAL_DIR / "model-cache.json"

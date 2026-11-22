from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "docs" / "animation" / "clinicalrag_grounding_sequence.json"
REEL = ROOT / "frontend" / "public" / "animation" / "clinicalrag-grounding-reel.html"


def test_clinicalrag_animation_exercises_grounding_and_safety() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/generate_clinicalrag_animation.py"],
        cwd=ROOT,
        env={**os.environ, "PYTHONPATH": str(ROOT / "backend")},
        check=True,
        capture_output=True,
        text=True,
    )
    assert "ingestion:" in result.stdout
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    reel = REEL.read_text(encoding="utf-8")
    assert manifest["source"]["synthetic"] is True
    assert manifest["source"]["document_count"] == 3
    assert manifest["grounded_query"]["safety_status"] == "allowed"
    assert manifest["grounded_query"]["citation_ids"]
    assert manifest["unsafe_query"]["classifier"]["allowed"] is False
    assert manifest["unsafe_query"]["trace"]["safety_status"] == "refused"
    assert manifest["evaluation"]["question_count"] == 3
    assert len(manifest["events"]) == 6
    assert "no patient data" in reel.lower()

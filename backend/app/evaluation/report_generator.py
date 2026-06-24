import json
from pathlib import Path
from app.core.config import settings

class EvaluationReportGenerator:
    def write(self, run_id: str, payload: dict) -> str:
        out_dir = settings.data_dir / 'reports'
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / f'evaluation_{run_id}.json'
        path.write_text(json.dumps(payload, indent=2), encoding='utf-8')
        return str(path)

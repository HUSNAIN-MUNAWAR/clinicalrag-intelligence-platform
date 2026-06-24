import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/'backend'))
from app.ingestion.source_adapters.demo_adapter import DemoSourceAdapter
from app.core.config import settings
if __name__ == '__main__':
    res=DemoSourceAdapter().download(settings.raw_dir)
    print({'files':[str(f) for f in res.files], 'license':res.license, 'notes':res.notes})

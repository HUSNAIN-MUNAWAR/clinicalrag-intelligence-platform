import os, sys, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault('DATABASE_URL', 'sqlite:///' + str(Path(tempfile.gettempdir())/'clinicalrag_test.db'))

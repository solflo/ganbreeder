import sys
from pathlib import Path

FROZEN = getattr(sys, "frozen", False)
_PKG = Path(__file__).resolve().parent
_ROOT = _PKG.parent

if FROZEN:
    _RES = Path(sys._MEIPASS)
    TEMPLATES_DIR = _RES / "templates"
    STATIC_DIR = _RES / "static"
    WEIGHTS_DIR = _RES / "weights"
    DATA_DIR = Path(sys.executable).resolve().parent / "data"
else:
    TEMPLATES_DIR = _PKG / "templates"
    STATIC_DIR = _PKG / "static"
    WEIGHTS_DIR = _ROOT / "weights"
    DATA_DIR = _ROOT / "data"

IMG_DIR = DATA_DIR / "img"
DB_PATH = DATA_DIR / "ganbreeder.db"

PORT = 8742
MODEL_NAME = "biggan-deep-256"

DIM_Z = 128
VOCAB_SIZE = 1000
TRUNCATION = 0.4
NUM_CHILDREN = 12
SEED_COUNT = 12


def ensure_dirs():
    IMG_DIR.mkdir(parents=True, exist_ok=True)

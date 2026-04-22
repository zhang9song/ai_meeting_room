from pathlib import Path

BASE_DIR = Path(__file__).parent

MEETINGS_DIR = BASE_DIR / "meetings"
MEETINGS_DIR.mkdir(exist_ok=True)

CONFIG_FILE = BASE_DIR / "config.yaml"

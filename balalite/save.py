import json
from pathlib import Path

SAVE_DIR = Path.home() / ".balalite"
SAVE_PATH = SAVE_DIR / "save.json"


def has_save():
    return SAVE_PATH.exists()


def save_game(game):
    SAVE_DIR.mkdir(parents=True, exist_ok=True)
    SAVE_PATH.write_text(json.dumps(game.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")


def load_game():
    from .game import GameState

    data = json.loads(SAVE_PATH.read_text(encoding="utf-8"))
    return GameState.from_dict(data)


def delete_save():
    if SAVE_PATH.exists():
        SAVE_PATH.unlink()

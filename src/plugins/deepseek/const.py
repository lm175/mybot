from pathlib import Path
import json

replies_path = Path(__file__).parent / 'resources' / 'replies.json'
with open(replies_path, 'r', encoding='utf-8') as f:
    replies: dict[str, list[str]] = json.load(f)
default_replies = replies['default_replies']
blocklist_resplies = replies['blocklist_resplies']
busy_replies = replies['busy_replies']
error_replies = replies['error_replies']
summarize_replies = replies['summarize_replies']
clear_replies = replies['clear_replies']


dir_path = Path("data/deepseek/")
if not dir_path.exists():
    dir_path.mkdir(parents=True, exist_ok=True)
character_path = dir_path / 'default_character.txt'
if not character_path.exists():
    character_path.touch()
with open(character_path, 'r', encoding='utf-8') as f:
    character = f.read()

blocklist_path = dir_path / 'blocklist.txt'
if not blocklist_path.exists():
    blocklist_path.touch()
with open(blocklist_path, 'r', encoding='utf-8') as f:
    blocklist = [line.strip() for line in f.readlines()]


morning_path = dir_path / 'morning'
if not morning_path.exists():
    morning_path.mkdir(parents=True, exist_ok=True)
night_path = dir_path / 'night'
if not night_path.exists():
    night_path.mkdir(parents=True, exist_ok=True)

images_path = dir_path / 'images'
if not images_path.exists():
    images_path.mkdir(parents=True, exist_ok=True)


__all__ = [
    "default_replies",
    "blocklist_resplies",
    "busy_replies",
    "error_replies",
    "summarize_replies",
    "clear_replies",
    "character",
    "blocklist",
    "morning_path",
    "night_path",
    "images_path",
]
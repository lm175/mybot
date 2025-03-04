from pathlib import Path


dir_path = Path("data/deepseek/")
if not dir_path.exists():
    dir_path.mkdir(parents=True, exist_ok=True)
character_path = dir_path / 'default_character.txt'
if not character_path.exists():
    character_path.touch()
with open(dir_path / 'default_character.txt', 'r', encoding='utf-8') as f:
    character = f.read()

blocklist_path = dir_path / 'blocklist.txt'
if not character_path.exists():
    character_path.touch()
with open(blocklist_path, 'r', encoding='utf-8') as file:
    blocklist = [line.strip() for line in file.readlines()]


morning_path = dir_path / 'morning'
if not morning_path.exists():
    morning_path.mkdir(parents=True, exist_ok=True)
night_path = dir_path / 'night'
if not night_path.exists():
    night_path.mkdir(parents=True, exist_ok=True)
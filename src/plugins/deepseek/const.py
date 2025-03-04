from pathlib import Path


dir_path = Path("data/deepseek/")
if not dir_path.exists():
    dir_path.mkdir(parents=True, exist_ok=True)
character_path = dir_path / 'default_character.txt'
if not character_path.exists():
    character_path.touch()
with open(dir_path / 'default_character.txt', 'r', encoding='utf-8') as f:
    character = f.read()


morning_path = dir_path / 'morning'
if not morning_path.exists():
    morning_path.mkdir(parents=True, exist_ok=True)
night_path = dir_path / 'night'
if not night_path.exists():
    night_path.mkdir(parents=True, exist_ok=True)


API_WARNING_TIP = '（系统提示：检测到不当内容，已自动终止对话）'
AUTHOR_WARNING_TIP = '（作者提示：若多次触发警告，您将会被加入黑名单）'
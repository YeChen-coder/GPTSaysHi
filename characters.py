"""Resolve the selected standalone character for setup and the avatar runtime."""
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def select_character(value=None, root=ROOT):
    catalog = json.loads((root / 'characters.json').read_text(encoding='utf-8'))
    if value is None:
        value = os.getenv('GPTSAYSHI_CHARACTER')
        if value is None:
            env = root / '.env'
            if env.is_file():
                for line in env.read_text(encoding='utf-8-sig').splitlines():
                    key, separator, setting = line.strip().partition('=')
                    if separator and key.strip() == 'GPTSAYSHI_CHARACTER':
                        value = setting.split(' #', 1)[0].strip().strip('\"\'')
        if value is None:
            value = catalog['default']
    for name, character in catalog['characters'].items():
        if name.lower() == value.strip().lower():
            return dict(character, name=name)
    raise ValueError('GPTSAYSHI_CHARACTER must be gentleman or QinChe')


if __name__ == '__main__':
    print(json.dumps(select_character()))

from pathlib import Path


HERE = Path(__file__)


for path in Path('.').rglob('*.py'):
    if path.name in ('yressir.py', 'write.py'):
        continue
    if str(path).startswith('build'):
        continue
    content = path.read_text()
    new_content = content.replace('from ..write import write', 'from ..write import WRITER').replace('write(', 'WRITER.write(')
    if content == new_content:
        continue
    print(f'Patching {path}')
    path.write_text(new_content)

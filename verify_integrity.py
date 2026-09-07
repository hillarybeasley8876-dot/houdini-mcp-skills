"""Verify all original bundle files against SHA256SUMS.txt; ignores newly generated files."""
from pathlib import Path
import hashlib

root=Path(__file__).resolve().parent
count=0
for line in (root/'SHA256SUMS.txt').read_text(encoding='utf-8').splitlines():
    expected, name=line.split('  ',1)
    path=root/name
    assert path.is_file(), f'Missing: {name}'
    assert hashlib.sha256(path.read_bytes()).hexdigest()==expected, f'Changed: {name}'
    count+=1
print(f'PASS: {count} files verified')

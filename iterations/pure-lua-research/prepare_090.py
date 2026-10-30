from pathlib import Path
import shutil
root=Path('work/vehicle-release-0.9.0');assert not root.exists();shutil.copytree('work/vehicle-release-0.8.0',root)
for p in root.rglob('*'):
 if p.is_file() and p.suffix in ('.lua','.md','.info'):
  p.write_text(p.read_text(encoding='utf-8-sig').replace('0.8.0','0.9.0'),encoding='utf-8')

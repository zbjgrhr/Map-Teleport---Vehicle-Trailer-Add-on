from pathlib import Path
s=Path('work/pure-lua-research/test_network_061.py').read_text(encoding='utf-8-sig').replace('work/vehicle-release-0.6.1','work/vehicle-candidate-0.8.0')
exec(compile(s,'candidate-normal-fallback','exec'))

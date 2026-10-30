from pathlib import Path
p=Path('work/vehicle-release-0.7.0/42/media/lua/client/UMV_RemoteSP.lua');s=p.read_text(encoding='utf-8-sig').replace('    s.remote=false\n    -- Keep','    s.remote=false\n    if success then P.progress=1 end\n    -- Keep').replace('Loading destination; vehicle protected at origin...','Loading destination; holding origin...');p.write_text(s,encoding='utf-8')

from pathlib import Path
p=Path('work/vehicle-release-0.7.0/42/media/lua/shared/UMV_Vehicle.lua');s=p.read_text();s=s.replace('    s.hops=s.hops+1;s.stepX=x;','    s.lastJumpDistance=distance(oldX,oldY,x,y)\n    s.hops=s.hops+1;s.stepX=x;');s=s.replace('" at=" .. x .. "," .. y)','" at=" .. x .. "," .. y .. " jumpDistance=" .. s.lastJumpDistance)');p.write_text(s,encoding='utf-8')
# Multiplayer regression against unchanged transport behavior and updated version handshake.
s=Path('work/pure-lua-research/test_network_061.py').read_text(encoding='utf-8-sig').replace('work/vehicle-release-0.6.1','work/vehicle-release-0.7.0')
exec(compile(s,'network-070','exec'))
# Existing person/animal/menu and legacy SP vehicle regressions.
s=Path('work/pure-lua-research/verify_release_060.py').read_text(encoding='utf-8-sig').replace('work/vehicle-release-0.6.0/42/media/lua','work/vehicle-release-0.7.0/42/media/lua').replace('client/UMV_Vehicle.lua','shared/UMV_Vehicle.lua')
exec(compile(s,'SP-070-regression','exec'))

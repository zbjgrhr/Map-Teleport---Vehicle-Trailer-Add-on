from pathlib import Path
import shutil
src=Path('work/vehicle-release-0.6.1');dst=Path('work/vehicle-release-0.6.2');assert not dst.exists();shutil.copytree(src,dst)
for p in dst.rglob('*'):
 if p.is_file() and p.suffix in ('.lua','.md','.info'):
  s=p.read_text(encoding='utf-8-sig').replace('0.6.1','0.6.2')
  if p.name=='UMV_Vehicle.lua':
   s=s.replace('= 96, 20000, 600000','= 128, 20000, 600000').replace('ipairs({96,80,64,56,48,40,32,24,18,12,8})','ipairs({128,112,96,80,64,56,48,40,32,24,18,12,8})')
  p.write_text(s,encoding='utf-8')
# Reuse the actual server + two-client simulation against this version's handshake.
s=Path('work/pure-lua-research/test_network_061.py').read_text(encoding='utf-8-sig').replace('work/vehicle-release-0.6.1','work/vehicle-release-0.6.2')
exec(compile(s,'network-062','exec'))
# Compare full journeys under the same wider loading window, not just candidate selection.
from lupa import LuaRuntime
fixture=Path('work/pure-lua-research/test_vehicle_steps.py').read_text().split("fixture=r'''",1)[1].split("'''",1)[0]
for version in ('0.6.1','0.6.2'):
 l=LuaRuntime();l.execute(fixture.replace('>48','>160'));l.execute('print=function()end')
 l.globals().P=l.execute(Path('work/vehicle-release-'+version+'/42/media/lua/shared/UMV_Vehicle.lua').read_text())
 l.execute('P.onStopped=function(ok,s)hops=s.hops end;assert(P.start(p,3100,2100));for i=1,20000 do frame();if not P.session then break end end;assert(P.progress==1,P.status);assert(unsafe==0 and not p.block)')
 print(version,'wide-window journey steps:',l.globals().hops)
# Narrow loaded windows must continue to shorten the attempted step.
l=LuaRuntime();l.execute(fixture);l.execute('print=function()end');l.globals().P=l.execute((dst/'42/media/lua/shared/UMV_Vehicle.lua').read_text())
l.execute('assert(P.start(p,3100,2100));for i=1,20000 do frame();if not P.session then break end end;assert(P.progress==1 and unsafe==0,P.status)')
print('PASS narrow-window fallback, loaded-only landings and controls restored')

from pathlib import Path
import shutil
root=Path('work/vehicle-release-0.6.3');assert not root.exists();shutil.copytree('work/vehicle-release-0.6.2',root)
for p in root.rglob('*'):
 if p.is_file() and p.suffix in ('.lua','.md','.info'):
  s=p.read_text(encoding='utf-8-sig').replace('0.6.2','0.6.3')
  if p.name=='UMV_Vehicle.lua':
   s=s.replace('= 128, 20000, 600000','= 512, 20000, 600000').replace('ipairs({128,112,96,80,64,56,48,40,32,24,18,12,8})','ipairs({512,384,256,192,160,128,112,96,80,64,56,48,40,32,24,18,12,8})')
   # Stop after the first successful length: later lengths cannot improve its forward progress.
   # Keep angle comparisons within that length; loaded-area checks still gate every candidate.
   s=s.replace('''        end
    end
    if best then return unpack(best) end''','''        end
        if best then return unpack(best) end
    end
    if best then return unpack(best) end''',1)
  p.write_text(s,encoding='utf-8')
# Validate long attempts in broad windows, and fallback in normal narrow ones.
import sys
sys.path.insert(0,str(Path('work/lua-test-deps').resolve()))
from lupa import LuaRuntime
fixture=Path('work/pure-lua-research/test_vehicle_steps.py').read_text().split("fixture=r'''",1)[1].split("'''",1)[0]
for window in [48,160,600]:
 l=LuaRuntime();l.execute(fixture.replace('>48','>'+str(window)));l.execute('print=function()end')
 l.globals().P=l.execute((root/'42/media/lua/shared/UMV_Vehicle.lua').read_text())
 l.execute('P.onStopped=function(ok,s)hops=s.hops end;assert(P.start(p,3100,2100));for i=1,20000 do frame();if not P.session then break end end;assert(P.progress==1 and unsafe==0 and not p.block,P.status)')
 print('Loaded half-window',window,'steps',l.globals().hops)
s=Path('work/pure-lua-research/test_network_061.py').read_text(encoding='utf-8-sig').replace('work/vehicle-release-0.6.1','work/vehicle-release-0.6.3');exec(compile(s,'network-063','exec'))

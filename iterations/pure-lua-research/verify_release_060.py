from pathlib import Path
import sys
sys.path.insert(0,str(Path('work/lua-test-deps').resolve()))
from lupa import LuaRuntime
from luaparser import ast
root=Path('work/vehicle-release-0.6.0/42/media/lua')
for p in root.rglob('*.lua'):ast.parse(p.read_text(encoding='utf-8-sig'))
# Existing lifecycle checks run against the actual release files after module renaming.
s=Path('work/pure-lua-research/test_015.py').read_text(encoding='utf-8-sig')
s=s.replace("root=Path('work/pure-lua-vehicle-test/42/media/lua')","root=Path('work/vehicle-release-0.6.0/42/media/lua')").replace("client/PLVT_Core.lua","client/UMV_Vehicle.lua").replace("shared/UMTSP_Animals.lua","shared/UMV_Animals.lua")
# Keep the historic baseline file name intact.
s=s.replace('outputs/PureLuaVehicleTest-0.1.4/UMTSPPureLuaVehicleTest/42/media/lua/client/UMV_Vehicle.lua','outputs/PureLuaVehicleTest-0.1.4/UMTSPPureLuaVehicleTest/42/media/lua/client/PLVT_Core.lua')
exec(compile(s,'release-animal-and-distance','exec'))
# Menu checks load the release's renamed modules and normal display labels.
s=Path('work/pure-lua-research/test_standalone_menu.py').read_text(encoding='utf-8-sig').split('original=Path(',1)[0]
s=s.replace('work/pure-lua-vehicle-test/42/media/lua','work/vehicle-release-0.6.0/42/media/lua')
for a,b in {'PLVT_Core':'UMV_Vehicle','UMTSP_Main':'UMV_Main','UMTSP_Animals':'UMV_Animals','UMTSP_PersonSeat':'UMV_PersonSeat'}.items():s=s.replace(a,b)
s=s.replace('Teleport Vehicle Here [Pure Lua Test]','Teleport Vehicle Here')
exec(compile(s,'release-menu','exec'))
# Larger window: verify 96-tile steps are used, while native destinations remain loaded.
fixture=Path('work/pure-lua-research/test_vehicle_steps.py').read_text().split("fixture=r'''",1)[1].split("'''",1)[0]
for label,path in [('0.1.5','work/pure-lua-vehicle-test/42/media/lua/client/PLVT_Core.lua'),('0.6.0',str(root/'client/UMV_Vehicle.lua'))]:
 l=LuaRuntime();l.execute(fixture.replace('>48','>112'));l.execute('print=function()end');l.globals().P=l.execute(Path(path).read_text())
 l.execute('P.onStopped=function(ok,s)hops=s.hops end;assert(P.start(p,3100,2100));for i=1,20000 do frame();if not P.session then frames=i;break end end;assert(P.progress==1,P.status);assert(unsafe==0)')
 print('Wider loaded window:',label,'steps',l.globals().hops,'frames',l.globals().frames)
print('PASS release Lua syntax, independent module names, normal menu labels, animals and distance checks')

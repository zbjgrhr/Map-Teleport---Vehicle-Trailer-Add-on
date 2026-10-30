from pathlib import Path
from lupa import LuaRuntime
# Load fixture without running the existing tests.
t=Path('work/pure-lua-research/test_vehicle_steps.py').read_text(encoding='utf-8-sig')
fixture=t.split("fixture=r'''",1)[1].split("'''\ndef runtime",1)[0]
core=Path('work/pure-lua-vehicle-test/42/media/lua/client/PLVT_Core.lua').read_text(encoding='utf-8-sig')
l=LuaRuntime();l.execute(fixture);l.globals().P=l.execute(core)
l.execute('''
local raw=cell.getGridSquare
function cell:getGridSquare(x,y,z)
 local sq=raw(self,x,y,z);if not sq then return end
 sq.isFree=function()return not(x>=102 and x<=140 and y>=80 and y<=122)end
 return sq
end
assert(P.start(p,200,100))
local detourSeen=false
for i=1,6000 do
 frame()
 if P.session and P.session.detourPath and #P.session.detourPath>0 then detourSeen=true end
 if not P.session then break end
end
assert(detourSeen,'did not exercise non-greedy detour')
assert(not P.session and P.progress==1,P.status)
assert(p.vehicle==nil and not p.block and saved==1 and unsafe==0)
''');print('PASS: temporary sideways/backward detour around an intermediate obstacle, then final arrival and exit')
l=LuaRuntime();l.execute(fixture);l.execute('Events={OnTick={Add=function()end}};function v:clearPassenger()self.seat=false end;v.removed=true;p.vehicle=v')
l.globals().Seat=l.execute(Path('work/pure-lua-vehicle-test/42/media/lua/shared/UMTSP_PersonSeat.lua').read_text(encoding='utf-8-sig'))
l.execute('assert(Seat.exit(p,v));assert(p.vehicle==nil and saved==0 and not v.seat)');print('PASS: stale NPC/player vehicle reference detached without invoking native exit or writing the DB')
# Marker regression uses the real copied base marker function.
menu=Path('work/pure-lua-research/test_standalone_menu.py').read_text(encoding='utf-8-sig')
# Its existing executable tests verify module wiring; extract only its Lua setup.
setup=menu.split("l.execute('''",1)[1].split("''')",1)[0]
l=LuaRuntime();l.execute(setup)
l.execute(Path('work/pure-lua-vehicle-test/42/media/lua/client/UMTSP_Main.lua').read_text(encoding='utf-8-sig'))
l.execute('''
markers={};removed=0;added=0
symbols={removeSymbol=function(s,m)markers[m]=nil;removed=removed+1 end,addTexture=function(s,kind,x,y)local m={x=x,y=y};setmetatable(m,{__index=function()return function()end end});markers[m]=true;added=added+1;return m end}
map.mapAPI.getSymbolsAPIv2=function()return symbols end
Pure.markVehicle(10,20);Pure.markVehicle(30,40)
local count=0;for m in pairs(markers)do count=count+1;assert(m.x==30 and m.y==40)end
assert(count==1 and added==2 and removed==1)
''');print('PASS: original steering-wheel marker replaces prior marker instead of accumulating')

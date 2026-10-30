from pathlib import Path
import sys
sys.path.insert(0,str(Path('work/lua-test-deps').resolve()))
from lupa import LuaRuntime
base=Path('work/pure-lua-research/test_vehicle_steps.py').read_text()
fixture=base.split("fixture=r'''",1)[1].split("'''",1)[0]
source=Path('work/pure-lua-vehicle-test/42/media/lua/client/PLVT_Core.lua').read_text()
def run(code,extra=''):
 l=LuaRuntime();l.execute(fixture);l.execute(extra);l.globals().P=l.execute(source);l.execute(code)
occupants='''
npc=setmetatable({x=p.x,y=p.y,z=0,block=true,data={},vehicle=v},{__index=p})
function v:getCharacter(index)if index==0 then return p.vehicle==self and p or nil end;return npc.vehicle==self and npc or nil end
function v:exit(actor)saved=saved+1;actor.vehicle=nil;return true end
'''
run('''assert(P.start(p,600,100));for i=1,2000 do frame();if P.session then assert(math.abs(p.x-npc.x)<1)else break end end
assert(P.progress==1 and not P.session,P.status)
assert(p.vehicle==nil and npc.vehicle==nil and saved==2)
assert(not p.block and npc.block and npc.data.PLVTGuard==nil)
assert(p.x~=npc.x or p.y~=npc.y,'occupants overlap')''',occupants)
print('PASS actual core: two seated occupants move together; separate exits; both movement locks restored')
run('''assert(P.start(p,600,100));for i=1,15 do frame()end;P.stop('cancel');assert(not P.session and p.vehicle==nil and npc.vehicle==nil and not p.block and npc.block)''',occupants)
print('PASS actual core: group cancellation saves and unlocks both occupants')
# Wide belt exceeds previous 24-tile greedy and 8-tile adjacent detour.
run('''assert(P.start(p,300,100));for i=1,3000 do frame();if not P.session then break end end;assert(P.progress==1,P.status);assert(unsafe==0)''','''
local oldSquare=square
function square(x,y)
 local result=oldSquare(x,y)
 if x>=110 and x<=138 then result.isFree=function()return false end end
 return result
end
''')
print('PASS actual core: jumps over obstacle belt using a fully loaded clear landing')

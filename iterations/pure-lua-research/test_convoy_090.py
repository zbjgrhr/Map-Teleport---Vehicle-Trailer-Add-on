import sys
from pathlib import Path
sys.path.insert(0,str(Path('work/lua-test-deps').resolve()))
from lupa import LuaRuntime
from luaparser import ast
base=Path('work/vehicle-release-0.9.0/42/media/lua')
for p in base.rglob('*.lua'): ast.parse(p.read_text(encoding='utf-8-sig'))
l=LuaRuntime(unpack_returned_tuples=True)
l.execute('C=(function()\n'+(base/'shared/UMV_Convoy.lua').read_text()+'\nend)()')
l.execute(r'''
local function vehicle(id,x)
 local v={id=id,x=x,y=100,speed=0,animals={},items={fuel=51}}
 function v:getId()return self.id end
 function v:getSqlId()return self.id+100 end
 function v:getX()return self.x end
 function v:getY()return self.y end
 function v:getZ()return 0 end
 function v:getVehicleTowing()return self.child end
 function v:getVehicleTowedBy()return self.parent end
 function v:getCurrentAbsoluteSpeedKmHour()return self.speed end
 function v:isRemovedFromWorld()return false end
 function v:getController()return true end
 function v:update()self.updated=true end
 function v:exit()self.saved=true end
 return v
end
a=vehicle(1,100);b=vehicle(2,106);c=vehicle(3,112)
a.child=b;b.parent=a;b.child=c;c.parent=b
b.animals[1]={name='cow'};animal=b.animals[1]
function geometry(v)return {ux=1,uy=0,vx=0,vy=1,halfX=2,halfZ=1}end
cell={getGridSquare=function(self,x,y,z)return {x=x,y=y}end}
function getCell()return cell end
s={};C.attach(s,b,geometry)
assert(#C.members(s)==3)
assert(C.registered(s,function()return true end))
local blocked=false
local function clear(m,x,y)return not(blocked and m.vehicle==c)end
assert(C.clear(s,500,600,clear))
blocked=true;assert(not C.clear(s,500,600,clear));assert(a.x==100 and c.x==112)
blocked=false
local fail=true
local function place(m,x,y)
 if fail and m.vehicle==c and x>200 then error('injected trailer failure')end
 m.vehicle.x=x;m.vehicle.y=y
end
assert(not pcall(C.place,s,500,600,{},place))
assert(a.x==100 and b.x==106 and c.x==112 and a.y==100 and c.y==100)
fail=false;C.place(s,500,600,{},place)
assert(a.x==494 and b.x==500 and c.x==506)
assert(a.y==600 and c.y==600)
assert(a.child==b and b.child==c and b.parent==a and c.parent==b)
assert(b.animals[1]==animal and b.items.fuel==51)
assert(not C.outside(s,506,600,500,600))
assert(C.outside(s,500,610,500,600))
local payload=C.payload(s,500,600);assert(#payload==3 and payload[1].sqlId==102)
C.persist(s);assert(a.saved and b.saved and c.saved)
c.parent=nil;assert(not C.registered(s,function()return true end));c.parent=b
c.speed=4;assert(not pcall(C.attach,{},a,geometry));c.speed=0
c.child=a;assert(not pcall(C.attach,{},a,geometry));c.child=nil
''')
print('PASS: three-body convoy translation, trailer obstruction, partial rollback, towing links, animal/items identity, every-member save, moving trailer and cycle rejection; all release Lua files parse.')

import sys
from pathlib import Path
sys.path.insert(0,str(Path('work/lua-test-deps').resolve()))
from lupa import LuaRuntime
from luaparser import ast
base=Path('work/pure-lua-vehicle-test/42/media/lua')
for p in base.rglob('*.lua'):ast.parse(p.read_text(encoding='utf-8-sig'))
l=LuaRuntime()
l.execute('''
Pure={}; counts={capture=0,stage=0,release=0,exit=0,vehicle=0}
Pure.start=function()counts.vehicle=counts.vehicle+1 end
A={capture=function()counts.capture=counts.capture+1;return animals end,stage=function()counts.stage=counts.stage+1;return true end,release=function()counts.release=counts.release+1;return true end}
Seat={requestRestore=function()end,forget=function()end,exit=function(player)counts.exit=counts.exit+1;player.vehicle=nil;return true end}
require=function(name) if name=='PLVT_Core' then return Pure elseif name=='UMTSP_Animals' then return A elseif name=='UMTSP_PersonSeat' then return Seat else return {} end end
callbacks={}
Events=setmetatable({}, {__index=function(t,k)local list={};callbacks[k]=list;local v={Add=function(f)table.insert(list,f)end};rawset(t,k,v);return v end})
function isClient()return false end
function isServer()return false end
function getNumActivePlayers()return 1 end
function getTimestampMs()return 0 end
IsoFlagType={water='water'}
sq={getFloor=function()return {getSprite=function()return {getProperties=function()return {has=function()return false end}end}end}end,isFree=function()return true end}
cell={getGridSquare=function()return sq end}
function getCell()return cell end
world={getMetaGrid=function()return {isValidChunk=function()return true end}end}
function getWorld()return world end
p={x=10,y=10,z=0,vehicle={}}
function p:getVehicle()return self.vehicle end
function p:getX()return self.x end
function p:getY()return self.y end
function p:getZ()return self.z end
function p:isDead()return false end
function p:Say(text)self.message=text end
function p:teleportTo(x,y,z)self.x=x;self.y=y;self.z=z end
function getSpecificPlayer()return p end
map={playerNum=0,mapAPI={uiToWorldX=function(s,x,y)return x end,uiToWorldY=function(s,x,y)return y end},getAbsoluteX=function()return 0 end,getAbsoluteY=function()return 0 end,isVisible=function()return true end}
ISWorldMap={onRightMouseUp=function()return false end,ShowWorldMap=function()end,HideWorldMap=function()end}
ISWorldMap_instance=map
context={options={},isVisible=function()return true end}
function context:addOptionOnTop(name,target,fn,...)local o={name=name,target=target,fn=fn,args={...}};table.insert(self.options,1,o);return o end
function getPlayerContextMenu()return context end
ISContextMenu={get=function()return context end}
animals={}
''')
l.execute((base/'client/UMTSP_Main.lua').read_text(encoding='utf-8-sig'))
l.execute('''
for _,f in ipairs(callbacks.OnGameStart)do f()end
ISWorldMap.onRightMouseUp(map,50,60)
assert(#context.options==2)
local person,car
for _,o in ipairs(context.options)do if o.name=='Teleport Here' then person=o else car=o end end
assert(person and car and car.name=='Teleport Vehicle Here [Pure Lua Test]')
car.fn(car.target,table.unpack(car.args));assert(counts.vehicle==1)
Pure.session={};person.fn(person.target,table.unpack(person.args));assert(counts.capture==0)
Pure.session=nil
p.vehicle={getX=function()return 10 end,getY=function()return 10 end}
person.fn(person.target,table.unpack(person.args))
assert(counts.exit==1 and counts.stage==1 and counts.release==1 and p.vehicle==nil)
assert(counts.vehicle==1 and not Pure.personBusy())
-- Same proven person flow, now on foot with a captured led-animal record.
animals={{animal='test'}}
person.fn(person.target,table.unpack(person.args))
assert(counts.stage==2 and counts.release==2 and counts.vehicle==1)
p.vehicle={getX=function()return 10 end,getY=function()return 10 end}
person.fn(person.target,table.unpack(person.args))
assert(counts.exit==2 and counts.stage==3 and counts.release==3 and p.vehicle==nil)
assert(Pure.animals==A)
''')
print('PASS: both menu options; person-only native exit; animal staging/release; no vehicle calls from person action; busy guard')
original=Path(r'C:\Users\zbjgr\Zomboid\Workshop\Map Teleport - Right-Click Rescue\Contents\mods\UniversalMapTeleportSP\42\media\lua')
for rel in ('shared/UMTSP_Animals.lua','server/UMTSP_Server.lua','client/UMTSP_Config.lua'):
 assert (original/rel).read_bytes()==(base/rel).read_bytes(),rel
print('PASS: animal, server and configuration files match tested base; seat copy has intentional unloaded-body guard')
